"""
validators.py — File upload validation for the ML service.

Validates content type and file size before passing the image to the
OpenAI vision model. Returning a 400 here causes Django to surface a
503 "ML service unavailable" to the frontend, so keep error messages clear.

Allowed types include image/webp because modern browsers (Chrome, Edge)
often upload photos as webp by default — excluding it causes silent failures
where valid uploads are rejected before reaching the AI model.
"""

from fastapi import UploadFile, HTTPException

# Accepted MIME types — must match ALLOWED_IMAGE_CONTENT_TYPES in Django settings.py
ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB — matches MAX_IMAGE_UPLOAD_SIZE in Django settings


async def validate_image(file: UploadFile):
    """
    Validate that the uploaded file is an allowed image type and within size limits.

    Reads the full file into memory to check size, then seeks back to the start
    so the caller can read it again for AI processing.

    Raises:
        HTTPException 400: if the content type is not allowed or file exceeds 5 MB.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image format. Allowed: {', '.join(ALLOWED_TYPES)}."
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB."
        )

    # Reset file pointer so the image can be read again downstream
    await file.seek(0)