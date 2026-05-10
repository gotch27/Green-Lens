import atexit
import shutil
import tempfile
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .ml_client import MLServiceUnavailable
from .models import Result, Scan


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
        "diagnosis": "Пепелница",
        "description": "Растението покажува симптоми на болест.",
        "characteristics": ["Бели дамки", "Суви рабови на листот"],
        "treatment_steps": ["Отстранете ги заразените делови", "Користете соодветен третман"],
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
        "recommendation": "Условите се прифатливи за третман.",
    }


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class HealthCheckTests(TestCase):
    def test_health_check_returns_expected_payload(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "message": "Server is active"})


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ScanApiTests(TestCase):
    @patch("scans.views.get_weather_for_city")
    @patch("scans.views.ml_client.analyze_image")
    def test_create_scan_returns_full_payload(self, analyze_image, get_weather_for_city):
        analyze_image.return_value = ml_payload()
        get_weather_for_city.return_value = weather_payload()

        response = self.client.post(
            "/api/scans/",
            {"image": image_upload(), "city": "Skopje"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["city"], "Skopje")
        self.assertEqual(data["diagnosis"], "Пепелница")
        self.assertEqual(data["weather"]["humidity"], 60)
        self.assertTrue(Scan.objects.filter(city="Skopje").exists())

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

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Invalid image format."})

    @override_settings(MAX_IMAGE_UPLOAD_SIZE=4)
    def test_create_scan_rejects_oversized_image(self):
        response = self.client.post(
            "/api/scans/",
            {"image": image_upload(), "city": "Skopje"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Image size too large."})

    @patch("scans.views.ml_client.analyze_image")
    def test_create_scan_maps_ml_failure(self, analyze_image):
        analyze_image.side_effect = MLServiceUnavailable("ML service unavailable.")

        response = self.client.post(
            "/api/scans/",
            {"image": image_upload(), "city": "Skopje"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"error": "ML service unavailable."})

    def test_history_returns_compact_payload(self):
        scan = self.create_scan()

        response = self.client.get("/api/scans/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["id"], scan.id)
        self.assertIn("image_url", response.json()[0])
        self.assertNotIn("treatment_steps", response.json()[0])

    def test_detail_returns_full_payload(self):
        scan = self.create_scan()

        response = self.client.get(f"/api/scans/{scan.id}/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], scan.id)
        self.assertEqual(data["treatment_steps"], ["Отстранете ги заразените делови"])

    def test_delete_scan_removes_history_item(self):
        scan = self.create_scan()

        response = self.client.delete(f"/api/scans/{scan.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Scan deleted successfully."})
        self.assertFalse(Scan.objects.filter(id=scan.id).exists())

    @patch("scans.views.get_weather_for_city")
    @patch("scans.views.ml_client.analyze_image")
    def test_retry_updates_result(self, analyze_image, get_weather_for_city):
        scan = self.create_scan()
        analyze_image.return_value = ml_payload(diagnosis="Пламеница", confidence=0.94)
        get_weather_for_city.return_value = weather_payload()

        response = self.client.post(f"/api/scans/{scan.id}/retry/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["diagnosis"], "Пламеница")
        scan.result.refresh_from_db()
        self.assertEqual(scan.result.confidence, 0.94)

    def test_report_returns_pdf(self):
        scan = self.create_scan()

        response = self.client.get(f"/api/scans/{scan.id}/report/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    @patch("scans.views.get_weather_for_city")
    def test_weather_endpoint_uses_city(self, get_weather_for_city):
        get_weather_for_city.return_value = weather_payload("Bitola")

        response = self.client.get("/api/weather/?city=Bitola")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["city"], "Bitola")

    def create_scan(self):
        scan = Scan.objects.create(
            city="Skopje",
            image=image_upload(),
            temperature=25.0,
            humidity=60,
            weather_recommendation="Условите се прифатливи за третман.",
        )
        Result.objects.create(
            scan=scan,
            is_sick=True,
            diagnosis="Пепелница",
            description="Растението покажува симптоми на болест.",
            characteristics=["Бели дамки"],
            treatment_steps=["Отстранете ги заразените делови"],
            links=["https://example.com"],
            confidence=0.89,
        )
        return scan
