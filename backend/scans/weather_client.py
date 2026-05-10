from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WeatherUnavailable(Exception):
    pass


def get_weather_for_city(city: str) -> dict[str, Any]:
    api_key = settings.OPENWEATHERMAP_API_KEY
    if not api_key:
        logger.error("OpenWeather API key is not configured.")
        raise WeatherUnavailable("Weather API key not configured.")

    try:
        logger.debug(
            "Requesting OpenWeather city=%s key_loaded=%s key_length=%s",
            city,
            bool(api_key),
            len(api_key),
        )
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=settings.WEATHER_TIMEOUT_SECONDS,
        )
        if not response.ok:
            logger.warning(
                "OpenWeather request failed city=%s status=%s body=%s",
                city,
                response.status_code,
                response.text[:500],
            )
            raise WeatherUnavailable("Weather service unavailable.")
        payload = response.json()
    except requests.Timeout as exc:
        logger.warning("OpenWeather request timed out city=%s", city)
        raise WeatherUnavailable("Weather service unavailable.") from exc
    except requests.RequestException as exc:
        logger.warning("OpenWeather request error city=%s error=%s", city, exc.__class__.__name__)
        raise WeatherUnavailable("Weather service unavailable.") from exc
    except ValueError as exc:
        logger.warning("OpenWeather returned invalid JSON city=%s", city)
        raise WeatherUnavailable("Weather service unavailable.") from exc
    except KeyError as exc:
        logger.warning("OpenWeather response missing expected field city=%s field=%s", city, exc)
        raise WeatherUnavailable("Weather service unavailable.") from exc

    temperature = float(payload["main"]["temp"])
    humidity = int(payload["main"]["humidity"])

    return {
        "city": city,
        "temperature": temperature,
        "humidity": humidity,
        "recommendation": build_weather_recommendation(temperature, humidity),
    }


def build_weather_recommendation(temperature: float, humidity: int) -> str:
    if humidity >= 80:
        return "Влажноста е висока. Одложете третман ако очекувате дожд или роса."
    if temperature >= 32:
        return "Температурата е висока. Третманот направете го рано наутро или доцна попладне."
    if temperature <= 5:
        return "Температурата е ниска. Проверете дали третманот е соодветен за овие услови."
    return "Условите се прифатливи за третман."
