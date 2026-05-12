from __future__ import annotations

import mimetypes
from secrets import token_urlsafe

from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.core.files.storage import default_storage
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import FileResponse, HttpResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from . import ml_client
from .models import GoogleAccount, Result, Scan
from .reports import build_scan_report
from .serializers import full_scan_payload, history_scan_payload
from .weather_client import WeatherUnavailable, get_weather_for_city

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()


def user_payload(user) -> dict:
    google_account = getattr(user, "google_account", None)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "avatar_url": google_account.avatar_url if google_account else "",
    }


def token_payload_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": user_payload(user),
    }


def username_from_email(email: str) -> str:
    local_part = email.split("@", 1)[0]
    base = "".join(ch if ch.isalnum() else "_" for ch in local_part).strip("_") or "user"
    username = base[:150]
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base[:145]}_{suffix}"[:150]
    return username


def users_with_email(email: str):
    return User.objects.filter(email__iexact=email).order_by("id")


def get_unique_user_by_email(email: str):
    matches = list(users_with_email(email)[:2])
    if len(matches) > 1:
        raise serializers.ValidationError(
            {"error": "Multiple users already use this email. Resolve duplicates before continuing."}
        )
    return matches[0] if matches else None


def verify_google_id_token(token: str) -> dict:
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    if not client_id:
        raise serializers.ValidationError({"error": "Google OAuth client id is not configured."})

    try:
        payload = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=client_id,
        )
    except ValueError as exc:
        raise serializers.ValidationError({"error": "Invalid Google ID token."}) from exc

    email = payload.get("email", "").strip().lower()
    subject = payload.get("sub", "").strip()
    if not email or not subject:
        raise serializers.ValidationError({"error": "Google account payload is missing required fields."})
    try:
        validate_email(email)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"error": "Google account payload has an invalid email."}) from exc
    if payload.get("email_verified") is not True:
        raise serializers.ValidationError({"error": "Google email is not verified."})

    return payload


def scan_queryset_for_request(request):
    return Scan.objects.filter(user=request.user)


def get_scan_or_404(scan_id, request):
    try:
        return scan_queryset_for_request(request).select_related("result").get(pk=scan_id)
    except (Scan.DoesNotExist, ObjectDoesNotExist):
        return None


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "message": "Server is active"})


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    email = data["email"].lower()

    if User.objects.filter(username=data["username"]).exists():
        return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)
    if users_with_email(email).exists():
        return Response({"error": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=data["username"],
                email=email,
                password=data["password"],
            )
    except IntegrityError:
        return Response({"error": "Unable to create user."}, status=status.HTTP_400_BAD_REQUEST)
    return Response(token_payload_for_user(user), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        request=request,
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )
    if user is None:
        return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(token_payload_for_user(user))


@api_view(["POST"])
@permission_classes([AllowAny])
def google_login(request):
    serializer = GoogleLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = verify_google_id_token(serializer.validated_data["id_token"])

    subject = payload["sub"].strip()
    email = payload["email"].strip().lower()
    first_name = payload.get("given_name", "").strip()
    last_name = payload.get("family_name", "").strip()
    avatar_url = payload.get("picture", "").strip()

    try:
        with transaction.atomic():
            google_account = (
                GoogleAccount.objects.select_for_update().select_related("user").filter(google_subject=subject).first()
            )
            user = google_account.user if google_account else get_unique_user_by_email(email)

            if user is None:
                user = User.objects.create_user(
                    username=username_from_email(email),
                    email=email,
                    password=token_urlsafe(32),
                    first_name=first_name,
                    last_name=last_name,
                )
            else:
                update_fields = []
                if user.email.lower() != email:
                    other_user = get_unique_user_by_email(email)
                    if other_user is not None and other_user.id != user.id:
                        raise serializers.ValidationError(
                            {"error": "This Google email is already linked to another user."}
                        )
                    user.email = email
                    update_fields.append("email")
                if user.first_name != first_name:
                    user.first_name = first_name
                    update_fields.append("first_name")
                if user.last_name != last_name:
                    user.last_name = last_name
                    update_fields.append("last_name")
                if update_fields:
                    user.save(update_fields=update_fields)

            existing_google_account = getattr(user, "google_account", None)
            if existing_google_account and existing_google_account.google_subject != subject:
                raise serializers.ValidationError(
                    {"error": "This user is already linked to a different Google account."}
                )

            GoogleAccount.objects.update_or_create(
                user=user,
                defaults={"google_subject": subject, "avatar_url": avatar_url},
            )
    except IntegrityError:
        return Response({"error": "Unable to link Google account."}, status=status.HTTP_400_BAD_REQUEST)

    return Response(token_payload_for_user(user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({"user": user_payload(request.user)})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def scans_collection(request):
    if request.method == "POST":
        return create_scan(request)

    scans = scan_queryset_for_request(request).select_related("result").order_by("-scanned_at")
    return Response([history_scan_payload(scan, request) for scan in scans])


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def scan_detail(request, scan_id):
    scan = get_scan_or_404(scan_id, request)
    if scan is None:
        return Response({"error": "Scan not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(full_scan_payload(scan, request))

    image = scan.image
    scan.delete()
    if image:
        image.delete(save=False)
    return Response({"message": "Scan deleted successfully."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def retry_scan(request, scan_id):
    scan = get_scan_or_404(scan_id, request)
    if scan is None:
        return Response({"error": "Scan not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        scan.image.open("rb")
        ml_payload = ml_client.analyze_image(scan.image)
    except ml_client.InvalidPlantImage as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except ml_client.MLServiceUnavailable:
        return Response({"error": "ML service unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except ml_client.InvalidMLResponse:
        return Response({"error": "ML service unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    finally:
        scan.image.close()

    Result.objects.update_or_create(scan=scan, defaults=ml_payload)
    apply_weather(scan, scan.city)
    return Response(full_scan_payload(get_scan_or_404(scan.id, request), request))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def scan_report(request, scan_id):
    scan = get_scan_or_404(scan_id, request)
    if scan is None:
        return Response({"error": "Scan not found."}, status=status.HTTP_404_NOT_FOUND)

    pdf = build_scan_report(scan)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="greenlens-scan-{scan.id}.pdf"'
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def scan_image(request, scan_id):
    scan = get_scan_or_404(scan_id, request)
    if scan is None or not scan.image:
        return Response({"error": "Scan not found."}, status=status.HTTP_404_NOT_FOUND)
    if not default_storage.exists(scan.image.name):
        return Response({"error": "Scan image not found."}, status=status.HTTP_404_NOT_FOUND)

    content_type = mimetypes.guess_type(scan.image.name)[0] or "application/octet-stream"
    return FileResponse(default_storage.open(scan.image.name, "rb"), content_type=content_type)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_weather(request):
    city = request.GET.get("city", "").strip()
    if not city:
        return Response({"error": "Missing city."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        return Response(get_weather_for_city(city))
    except WeatherUnavailable as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_scan(request):
    image = request.FILES.get("image")
    city = request.data.get("city", "").strip()
    error = validate_image(image)
    if error:
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

    try:
        ml_payload = ml_client.analyze_image(image)
    except ml_client.InvalidPlantImage as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except ml_client.MLServiceUnavailable:
        return Response({"error": "ML service unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except ml_client.InvalidMLResponse:
        return Response({"error": "ML service unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    scan = Scan.objects.create(user=request.user, city=city, image=image)
    Result.objects.create(scan=scan, **ml_payload)
    apply_weather(scan, city)
    scan = get_scan_or_404(scan.id, request)
    return Response(full_scan_payload(scan, request), status=status.HTTP_201_CREATED)


def validate_image(image) -> str | None:
    if image is None:
        return "Invalid image format."
    if image.size > settings.MAX_IMAGE_UPLOAD_SIZE:
        return "Image size too large."
    if image.content_type not in settings.ALLOWED_IMAGE_CONTENT_TYPES:
        return "Invalid image format."

    try:
        Image.open(image).verify()
    except (UnidentifiedImageError, OSError):
        return "Invalid image format."
    finally:
        image.seek(0)

    return None


def apply_weather(scan: Scan, city: str) -> None:
    if not city:
        return
    try:
        weather = get_weather_for_city(city)
    except WeatherUnavailable:
        scan.weather_recommendation = ""
        scan.save(update_fields=["weather_recommendation"])
        return

    scan.temperature = weather["temperature"]
    scan.humidity = weather["humidity"]
    scan.weather_recommendation = weather["recommendation"]
    scan.save(update_fields=["temperature", "humidity", "weather_recommendation"])
