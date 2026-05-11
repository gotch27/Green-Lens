import atexit
import json
import shutil
import tempfile
from io import BytesIO
from unittest.mock import Mock
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework_simplejwt.tokens import RefreshToken

from . import ml_client
from .ml_client import MLServiceUnavailable
from .models import GoogleAccount, Result, Scan

User = get_user_model()

TEST_MEDIA_ROOT = tempfile.mkdtemp()
atexit.register(lambda: shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True))


def image_upload(name="leaf.jpg", content_type="image/jpeg"):
    image = Image.new("RGB", (8, 8), color="green")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


def ml_payload(**overrides):
    payload = {
        "is_sick": True,
        "diagnosis": "Powdery mildew",
        "description": "The plant shows visible signs of disease.",
        "characteristics": ["White patches", "Dry damage on the leaves"],
        "treatment_steps": ["Remove infected leaves", "Apply a suitable treatment"],
        "links": ["https://example.com"],
        "confidence": 0.89,
    }
    payload.update(overrides)
    return payload


def weather_payload(city="Skopje"):
    return {
        "city": city,
        "temperature": 25.0,
        "humidity": 60,
        "recommendation": "Conditions are acceptable for treatment.",
    }


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class HealthCheckTests(TestCase):
    def test_health_check_returns_expected_payload(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "message": "Server is active"})


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, ML_SERVICE_URL="http://ml-service:8001", ML_SERVICE_TIMEOUT_SECONDS=5)
class MLClientTests(TestCase):
    @patch("scans.ml_client.requests.post")
    def test_analyze_image_guesses_content_type_for_saved_image(self, post):
        response = Mock()
        response.status_code = 200
        response.json.return_value = ml_payload()
        post.return_value = response
        image_file = BytesIO(b"fake image bytes")
        image_file.name = "scans/leaf.jpg"

        ml_client.analyze_image(image_file)

        files = post.call_args.kwargs["files"]
        self.assertEqual(files["image"][2], "image/jpeg")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ScanApiTests(TestCase):
    def auth_headers(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    @patch("scans.views.get_weather_for_city")
    @patch("scans.views.ml_client.analyze_image")
    def test_create_scan_returns_full_payload(self, analyze_image, get_weather_for_city):
        user = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        analyze_image.return_value = ml_payload()
        get_weather_for_city.return_value = weather_payload()

        response = self.client.post(
            "/api/scans/",
            {"image": image_upload(), "city": "Skopje"},
            **self.auth_headers(user),
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["city"], "Skopje")
        self.assertEqual(data["diagnosis"], "Powdery mildew")
        self.assertEqual(data["weather"]["humidity"], 60)
        self.assertTrue(Scan.objects.filter(city="Skopje").exists())

    @patch("scans.views.get_weather_for_city")
    @patch("scans.views.ml_client.analyze_image")
    def test_create_scan_assigns_authenticated_user(self, analyze_image, get_weather_for_city):
        user = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        analyze_image.return_value = ml_payload()
        get_weather_for_city.return_value = weather_payload()

        response = self.client.post(
            "/api/scans/",
            {"image": image_upload(), "city": "Skopje"},
            **self.auth_headers(user),
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Scan.objects.filter(city="Skopje", user=user).exists())

    def test_scan_endpoints_require_authentication(self):
        response = self.client.get("/api/scans/")

        self.assertEqual(response.status_code, 401)

    def test_create_scan_rejects_invalid_file_type(self):
        response = self.client.post(
            "/api/scans/",
            {
                "image": SimpleUploadedFile(
                    "leaf.txt",
                    b"not an image",
                    content_type="text/plain",
                ),
                "city": "Skopje",
            },
        )

        self.assertEqual(response.status_code, 401)

    @override_settings(MAX_IMAGE_UPLOAD_SIZE=4)
    def test_create_scan_rejects_oversized_image(self):
        user = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        response = self.client.post(
            "/api/scans/",
            {"image": image_upload(), "city": "Skopje"},
            **self.auth_headers(user),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Image size too large."})

    @patch("scans.views.ml_client.analyze_image")
    def test_create_scan_maps_ml_failure(self, analyze_image):
        user = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        analyze_image.side_effect = MLServiceUnavailable("ML service unavailable.")

        response = self.client.post(
            "/api/scans/",
            {"image": image_upload(), "city": "Skopje"},
            **self.auth_headers(user),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"error": "ML service unavailable."})

    def test_history_returns_compact_payload(self):
        user = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        scan = self.create_scan(user=user)

        response = self.client.get("/api/scans/", **self.auth_headers(user))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["id"], scan.id)
        self.assertIn("image_url", response.json()[0])
        self.assertNotIn("treatment_steps", response.json()[0])

    def test_authenticated_history_only_returns_own_scans(self):
        owner = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        other_user = User.objects.create_user(username="other", email="other@example.com", password="password123")
        own_scan = self.create_scan(user=owner)
        self.create_scan(user=other_user)

        response = self.client.get("/api/scans/", **self.auth_headers(owner))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [own_scan.id])

    def test_detail_returns_full_payload(self):
        user = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        scan = self.create_scan(user=user)

        response = self.client.get(f"/api/scans/{scan.id}/", **self.auth_headers(user))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], scan.id)
        self.assertEqual(data["treatment_steps"], ["Remove infected leaves"])

    def test_authenticated_user_cannot_access_other_users_scan(self):
        owner = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        other_user = User.objects.create_user(username="other", email="other@example.com", password="password123")
        scan = self.create_scan(user=other_user)

        response = self.client.get(f"/api/scans/{scan.id}/", **self.auth_headers(owner))

        self.assertEqual(response.status_code, 404)

    def test_deleting_user_deletes_owned_scans(self):
        user = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        scan = self.create_scan(user=user)

        user.delete()

        self.assertFalse(Scan.objects.filter(id=scan.id).exists())

    def test_delete_scan_removes_history_item(self):
        user = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        scan = self.create_scan(user=user)

        response = self.client.delete(f"/api/scans/{scan.id}/", **self.auth_headers(user))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Scan deleted successfully."})
        self.assertFalse(Scan.objects.filter(id=scan.id).exists())

    @patch("scans.views.get_weather_for_city")
    @patch("scans.views.ml_client.analyze_image")
    def test_retry_updates_result(self, analyze_image, get_weather_for_city):
        user = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        scan = self.create_scan(user=user)
        analyze_image.return_value = ml_payload(diagnosis="Blight", confidence=0.94)
        get_weather_for_city.return_value = weather_payload()

        response = self.client.post(f"/api/scans/{scan.id}/retry/", **self.auth_headers(user))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["diagnosis"], "Blight")
        scan.result.refresh_from_db()
        self.assertEqual(scan.result.confidence, 0.94)

    def test_report_returns_pdf(self):
        user = User.objects.create_user(username="owner", email="owner@example.com", password="password123")
        scan = self.create_scan(user=user)

        response = self.client.get(f"/api/scans/{scan.id}/report/", **self.auth_headers(user))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    @patch("scans.views.get_weather_for_city")
    def test_weather_endpoint_uses_city(self, get_weather_for_city):
        get_weather_for_city.return_value = weather_payload("Bitola")

        response = self.client.get("/api/weather/?city=Bitola")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["city"], "Bitola")

    def create_scan(self, user=None):
        scan = Scan.objects.create(
            user=user,
            city="Skopje",
            image=image_upload(),
            temperature=25.0,
            humidity=60,
            weather_recommendation="Conditions are acceptable for treatment.",
        )
        Result.objects.create(
            scan=scan,
            is_sick=True,
            diagnosis="Powdery mildew",
            description="The plant shows visible signs of disease.",
            characteristics=["White patches"],
            treatment_steps=["Remove infected leaves"],
            links=["https://example.com"],
            confidence=0.89,
        )
        return scan


class AuthApiTests(TestCase):
    def test_register_returns_jwt_tokens(self):
        response = self.client.post(
            "/api/auth/register/",
            data=json.dumps(
                {
                    "username": "farmer",
                    "email": "farmer@example.com",
                    "password": "password123",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())
        self.assertEqual(response.json()["user"]["username"], "farmer")

    def test_login_returns_jwt_tokens(self):
        User.objects.create_user(username="farmer", email="farmer@example.com", password="password123")

        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "farmer", "password": "password123"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_register_rejects_duplicate_email_case_insensitively(self):
        User.objects.create_user(username="existing", email="Farmer@Example.com", password="password123")

        response = self.client.post(
            "/api/auth/register/",
            data=json.dumps(
                {
                    "username": "farmer2",
                    "email": "farmer@example.com",
                    "password": "password123",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Email already exists."})

    def test_me_returns_authenticated_user(self):
        user = User.objects.create_user(username="farmer", email="farmer@example.com", password="password123")
        token = str(RefreshToken.for_user(user).access_token)

        response = self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {token}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["email"], "farmer@example.com")

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="google-client-id.apps.googleusercontent.com")
    @patch("scans.views.id_token.verify_oauth2_token")
    def test_google_login_creates_or_maps_user(self, verify_oauth2_token):
        verify_oauth2_token.return_value = {
            "sub": "google-subject-1",
            "email": "farmer@example.com",
            "given_name": "Geo",
            "family_name": "Farmer",
            "picture": "https://example.com/avatar.png",
        }

        response = self.client.post(
            "/api/auth/google/",
            data=json.dumps({"id_token": "google-id-token"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email="farmer@example.com").exists())
        self.assertTrue(GoogleAccount.objects.filter(google_subject="google-subject-1").exists())
        self.assertIn("access", response.json())

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="google-client-id.apps.googleusercontent.com")
    @patch("scans.views.id_token.verify_oauth2_token")
    def test_google_login_rejects_ambiguous_email_matches(self, verify_oauth2_token):
        User.objects.create_user(username="farmer1", email="farmer@example.com", password="password123")
        User.objects.create_user(username="farmer2", email="Farmer@Example.com", password="password123")
        verify_oauth2_token.return_value = {
            "sub": "google-subject-1",
            "email": "farmer@example.com",
            "given_name": "Geo",
            "family_name": "Farmer",
            "picture": "https://example.com/avatar.png",
        }

        response = self.client.post(
            "/api/auth/google/",
            data=json.dumps({"id_token": "google-id-token"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"error": "Multiple users already use this email. Resolve duplicates before continuing."},
        )

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="google-client-id.apps.googleusercontent.com")
    @patch("scans.views.id_token.verify_oauth2_token")
    def test_google_login_rejects_invalid_google_token(self, verify_oauth2_token):
        verify_oauth2_token.side_effect = ValueError("bad token")

        response = self.client.post(
            "/api/auth/google/",
            data=json.dumps({"id_token": "google-id-token"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Invalid Google ID token."})
