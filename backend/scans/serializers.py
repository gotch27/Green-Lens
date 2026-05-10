from __future__ import annotations


def image_url(request, scan) -> str:
    return scan.image.url if scan.image else ""


def weather_payload(scan) -> dict | None:
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
    result = scan.result
    return {
        "id": scan.id,
        "image_url": image_url(request, scan),
        "city": scan.city,
        "is_sick": result.is_sick,
        "diagnosis": result.diagnosis,
        "description": result.description,
        "characteristics": result.characteristics,
        "treatment_steps": result.treatment_steps,
        "links": result.links,
        "confidence": result.confidence,
        "weather": weather_payload(scan),
        "created_at": scan.scanned_at.isoformat().replace("+00:00", "Z"),
    }


def history_scan_payload(scan, request=None) -> dict:
    result = getattr(scan, "result", None)
    return {
        "id": scan.id,
        "image_url": image_url(request, scan),
        "city": scan.city,
        "is_sick": result.is_sick if result else None,
        "diagnosis": result.diagnosis if result else None,
        "created_at": scan.scanned_at.isoformat().replace("+00:00", "Z"),
    }
