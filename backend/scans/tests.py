from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase

from .models import Result, Scan


class HealthCheckTests(TestCase):
    def test_health_check_returns_expected_payload(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "message": "Server is active"})


class ScanResultModelTests(TestCase):
    def test_result_is_one_to_one_with_scan(self):
        user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password="password123",
        )
        scan = Scan.objects.create(
            user=user,
            location="Skopje",
            image=SimpleUploadedFile("leaf.jpg", b"fake-image-content", content_type="image/jpeg"),
        )
        Result.objects.create(scan=scan, diagnosis="Rust", recommendation="Apply treatment.")

        with self.assertRaises(IntegrityError):
            Result.objects.create(scan=scan, diagnosis="Blight", recommendation="Do not duplicate.")
