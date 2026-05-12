from __future__ import annotations

import mimetypes
from typing import Any

import requests
from django.conf import settings


class MLServiceUnavailable(Exception):
    pass


class InvalidMLResponse(Exception):
    pass


class InvalidPlantImage(Exception):
    pass


REQUIRED_KEYS = {
    "is_sick",
    "diagnosis",
    "description",
    "characteristics",
    "treatment_steps",
    "links",
    "confidence",
}


def analyze_image(image_file) -> dict[str, Any]:
    url = settings.ML_SERVICE_URL.rstrip("/") + "/ml/analyze/"
    image_file.seek(0)
    files = {
        "image": (
            image_file.name,
            image_file,
            get_image_content_type(image_file),
        )
    }

    try:
        response = requests.post(url, files=files, timeout=settings.ML_SERVICE_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise MLServiceUnavailable("ML service unavailable.") from exc
    finally:
        image_file.seek(0)

    if response.status_code >= 500:
        raise MLServiceUnavailable("ML service unavailable.")
    if response.status_code == 422:
        raise InvalidPlantImage(
            error_detail(response) or "Сликата не изгледа како растение. Прикачете јасна фотографија од растение."
        )
    if response.status_code >= 400:
        raise InvalidMLResponse("Invalid ML response.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise InvalidMLResponse("Invalid ML response.") from exc

    return validate_ml_payload(payload)


def get_image_content_type(image_file) -> str:
    content_type = getattr(image_file, "content_type", None)

    if content_type:
        return content_type

    guessed_type, _ = mimetypes.guess_type(image_file.name)
    return guessed_type or "application/octet-stream"


def error_detail(response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return ""

    detail = payload.get("detail") if isinstance(payload, dict) else None
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict):
            return str(first.get("msg") or first)
        return str(first)
    return ""


def validate_ml_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or not REQUIRED_KEYS.issubset(payload.keys()):
        raise InvalidMLResponse("Invalid ML response.")

    if payload.get("is_plant") is False:
        raise InvalidPlantImage(
            payload.get("non_plant_reason") or "Сликата не изгледа како растение. Прикачете јасна фотографија од растение."
        )

    if not isinstance(payload["is_sick"], bool):
        raise InvalidMLResponse("Invalid ML response.")

    for key in ("characteristics", "treatment_steps", "links"):
        if not isinstance(payload[key], list):
            raise InvalidMLResponse("Invalid ML response.")

    confidence = payload["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise InvalidMLResponse("Invalid ML response.")

    return {
        "is_sick": payload["is_sick"],
        "diagnosis": payload["diagnosis"],
        "description": payload["description"] or "",
        "characteristics": payload["characteristics"],
        "treatment_steps": payload["treatment_steps"],
        "links": payload["links"],
        "confidence": float(confidence),
    }
