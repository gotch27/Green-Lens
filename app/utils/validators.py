from fastapi import UploadFile, HTTPException

ALLOWED_TYPES = ["image/jpeg", "image/png"]

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


async def validate_image(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid image format."
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Image too large."
        )

    await file.seek(0)