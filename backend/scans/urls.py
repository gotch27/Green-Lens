from django.urls import path

from .views import get_weather, health_check, retry_scan, scan_detail, scan_report, scans_collection


urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("scans/", scans_collection, name="scans-collection"),
    path("scans/<int:scan_id>/", scan_detail, name="scan-detail"),
    path("scans/<int:scan_id>/retry/", retry_scan, name="scan-retry"),
    path("scans/<int:scan_id>/report/", scan_report, name="scan-report"),
    path("weather/", get_weather, name="weather"),
]
