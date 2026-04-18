from django.urls import path

from .views import health_check
from .views import get_weather


urlpatterns = [
    path("health/", health_check, name="health-check"),
    path('weather/', get_weather),
]
