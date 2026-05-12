from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from services.openai_service import NonPlantImageError, analyze_plant_image
from utils.validators import validate_image

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "diagnosis_prompt.txt"

app = FastAPI()


@app.get("/")
def root():
    return {"message": "GreenLens ML Service Running"}


@app.post("/ml/analyze/")
async def analyze_image(image: UploadFile = File(...)):
    try:
        await validate_image(image)
        image_bytes = await image.read()

        with PROMPT_PATH.open("r", encoding="utf-8") as file:
            prompt_text = file.read()

        result = analyze_plant_image(image_bytes, prompt_text, image.content_type or "image/jpeg")

        return result

    except NonPlantImageError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
