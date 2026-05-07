from fastapi import FastAPI, UploadFile, File, HTTPException

from app.utils.validators import validate_image
from app.services.openai_service import analyze_plant_image

app = FastAPI()


@app.get("/")
def root():
    return {"message": "GreenLens ML Service Running"}


@app.post("/ml/analyze/")
async def analyze_image(image: UploadFile = File(...)):
    try:
        # validate image
        await validate_image(image)

        # read image
        image_bytes = await image.read()

        # load prompt
        with open(
            "app/prompts/diagnosis_prompt.txt",
            "r",
            encoding="utf-8"
        ) as file:
            prompt_text = file.read()

        # analyze image
        result = analyze_plant_image(image_bytes, prompt_text)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )