from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Scan(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="scans",
        null=True,
        blank=True,
    )
    city = models.CharField(max_length=255, blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="scans/")
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.PositiveIntegerField(null=True, blank=True)
    weather_recommendation = models.TextField(blank=True)

    def __str__(self) -> str:
        city = self.city or "No city"
        return f"Scan #{self.pk} - {city}"


class Result(models.Model):
    scan = models.OneToOneField(Scan, on_delete=models.CASCADE, related_name="result")
    is_sick = models.BooleanField()
    diagnosis = models.TextField(null=True, blank=True)
    description = models.TextField(blank=True)
    characteristics = models.JSONField(default=list, blank=True)
    treatment_steps = models.JSONField(default=list, blank=True)
    links = models.JSONField(default=list, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Result for Scan #{self.scan_id}"


class GoogleAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="google_account")
    google_subject = models.CharField(max_length=255, unique=True)
    avatar_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Google account for {self.user.username}"
