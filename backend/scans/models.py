from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Scan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scans")
    location = models.CharField(max_length=255)
    scanned_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="scans/")

    def __str__(self) -> str:
        return f"Scan #{self.pk} - {self.location}"


class Result(models.Model):
    scan = models.OneToOneField(Scan, on_delete=models.CASCADE, related_name="result")
    diagnosis = models.TextField()
    recommendation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Result for Scan #{self.scan_id}"
