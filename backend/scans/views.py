from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import ml_client
from .models import Result, Scan
from .reports import build_scan_report
from .serializers import full_scan_payload, history_scan_payload
from .weather_client import WeatherUnavailable, get_weather_for_city


def health_check(request):
    return JsonResponse({"status": "ok", "message": "Server is active"})


@csrf_exempt
def scans_collection(request):
    if request.method == "POST":
        return create_scan(request)
    if request.method == "GET":
        scans = Scan.objects.select_related("result").order_by("-scanned_at")
        return JsonResponse([history_scan_payload(scan, request) for scan in scans], safe=False)
    return JsonResponse({"error": "Method not allowed."}, status=405)


@csrf_exempt
def scan_detail(request, scan_id):
    scan = get_scan_or_404(scan_id)
    if scan is None:
        return JsonResponse({"error": "Scan not found."}, status=404)

    if request.method == "GET":
        return JsonResponse(full_scan_payload(scan, request))

    if request.method == "DELETE":
        image = scan.image
        scan.delete()
        if image:
            image.delete(save=False)
        return JsonResponse({"message": "Scan deleted successfully."})

    return JsonResponse({"error": "Method not allowed."}, status=405)


@csrf_exempt
def retry_scan(request, scan_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    scan = get_scan_or_404(scan_id)
    if scan is None:
        return JsonResponse({"error": "Scan not found."}, status=404)

    try:
        scan.image.open("rb")
        ml_payload = ml_client.analyze_image(scan.image)
    except ml_client.MLServiceUnavailable:
        return JsonResponse({"error": "ML service unavailable."}, status=503)
    except ml_client.InvalidMLResponse:
        return JsonResponse({"error": "ML service unavailable."}, status=503)
    finally:
        scan.image.close()

    Result.objects.update_or_create(scan=scan, defaults=ml_payload)
    apply_weather(scan, scan.city)
    return JsonResponse(full_scan_payload(get_scan_or_404(scan.id), request))


def scan_report(request, scan_id):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    scan = get_scan_or_404(scan_id)
    if scan is None:
        return JsonResponse({"error": "Scan not found."}, status=404)

    pdf = build_scan_report(scan)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="greenlens-scan-{scan.id}.pdf"'
    return response


def get_weather(request):
    city = request.GET.get("city", "").strip()
    if not city:
        return JsonResponse({"error": "Missing city."}, status=400)
    try:
        return JsonResponse(get_weather_for_city(city))
    except WeatherUnavailable as exc:
        return JsonResponse({"error": str(exc)}, status=500)


def create_scan(request):
    image = request.FILES.get("image")
    city = request.POST.get("city", "").strip()
    error = validate_image(image)
    if error:
        return JsonResponse({"error": error}, status=400)

    try:
        ml_payload = ml_client.analyze_image(image)
    except ml_client.MLServiceUnavailable:
        return JsonResponse({"error": "ML service unavailable."}, status=503)
    except ml_client.InvalidMLResponse:
        return JsonResponse({"error": "ML service unavailable."}, status=503)

    user = request.user if request.user.is_authenticated else None
    scan = Scan.objects.create(user=user, city=city, image=image)
    Result.objects.create(scan=scan, **ml_payload)
    apply_weather(scan, city)
    scan = get_scan_or_404(scan.id)
    return JsonResponse(full_scan_payload(scan, request), status=201)


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


def get_scan_or_404(scan_id):
    try:
        return Scan.objects.select_related("result").get(pk=scan_id)
    except (Scan.DoesNotExist, ObjectDoesNotExist):
        return None
