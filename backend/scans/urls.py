from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    get_weather,
    google_login,
    health_check,
    login_view,
    me,
    register_view,
    retry_scan,
    scan_detail,
    scan_report,
    scans_collection,
)


urlpatterns = [
    path("auth/register/", register_view, name="auth-register"),
    path("auth/login/", login_view, name="auth-login"),
    path("auth/google/", google_login, name="auth-google"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", me, name="auth-me"),
    path("health/", health_check, name="health-check"),
    path("scans/", scans_collection, name="scans-collection"),
    path("scans/<int:scan_id>/", scan_detail, name="scan-detail"),
    path("scans/<int:scan_id>/retry/", retry_scan, name="scan-retry"),
    path("scans/<int:scan_id>/report/", scan_report, name="scan-report"),
    path("weather/", get_weather, name="weather"),
]
