"""
serializers.py — Plain-function serializers for Scan model responses.

Uses functions instead of DRF ModelSerializer classes for explicit control
over the response shape and to avoid over-fetching related objects.

Image URL strategy:
    We return scan.image.url (the /media/ path) instead of a protected API
    endpoint, because <img> tags in the browser cannot attach Bearer tokens.
    Django serves /media/ files directly in DEBUG mode via urls.py.
"""

from __future__ import annotations


def image_url(request, scan) -> str:
    """
    Return the public /media/ URL for the scan's uploaded image.

    NOTE: We intentionally do NOT return an authenticated API endpoint here.
    HTML <img> tags cannot send Authorization headers, so the image must be
    accessible without a token. Django serves /media/ in DEBUG mode via
    `static(settings.MEDIA_URL, ...)` added in greenlens/urls.py.
    """
    if not scan.image:
        return ""
    return scan.image.url


def weather_payload(scan) -> dict | None:
    """
    Build the weather sub-object for a scan response.
    Returns None if no city was recorded with the scan.
    Temperature/humidity can be None if the weather API call failed or timed out.
    """
    if not scan.city:
        return None
    if scan.temperature is None or scan.humidity is None:
        return {
            "city": scan.city,
            "temperature": None,
            "humidity": None,
            "recommendation": scan.weather_recommendation,
        }
    return {
        "city": scan.city,
        "temperature": scan.temperature,
        "humidity": scan.humidity,
        "recommendation": scan.weather_recommendation,
    }


def full_scan_payload(scan, request=None) -> dict:
    """
    Full scan response — used for POST (new scan) and GET /scans/:id/.
    Includes all diagnosis fields, treatment steps, and weather data.
    """
    result = scan.result
    return {
        "id": scan.id,
        "image_url": image_url(request, scan),
        "city": scan.city,
        "is_sick": result.is_sick,
        "diagnosis": result.diagnosis,           # Macedonian Cyrillic text
        "description": result.description,       # Macedonian Cyrillic text
        "characteristics": result.characteristics,  # List of symptom strings
        "treatment_steps": result.treatment_steps,  # List of action strings
        "links": result.links,                   # Always [] — populated by another service
        "confidence": result.confidence,         # Float 0.0–1.0
        "weather": weather_payload(scan),
        "created_at": scan.scanned_at.isoformat().replace("+00:00", "Z"),
    }


def history_scan_payload(scan, request=None) -> dict:
    """
    Compact scan response — used for GET /scans/ (history list).
    Omits heavy fields (description, treatment_steps, etc.) to keep
    the list response lightweight.
    """
    result = getattr(scan, "result", None)
    return {
        "id": scan.id,
        "image_url": image_url(request, scan),
        "city": scan.city,
        "is_sick": result.is_sick if result else None,
        "diagnosis": result.diagnosis if result else None,
        "created_at": scan.scanned_at.isoformat().replace("+00:00", "Z"),
    }
