import base64
import os

from dotenv import load_dotenv
from openai import OpenAI

from models.diagnosis_schema import PlantDiagnosis
from services.web_search_service import search_disease_links

load_dotenv()

NON_PLANT_MESSAGE = "Сликата не изгледа како растение. Прикачете јасна фотографија од растение."


class NonPlantImageError(ValueError):
    pass


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required to analyze plant images.")

    return OpenAI(api_key=api_key)


def analyze_plant_image(image_bytes, prompt_text, content_type="image/jpeg"):
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = get_openai_client().responses.parse(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": prompt_text
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Analyze this plant image."
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:{content_type};base64,{base64_image}"
                    }
                ]
            }
        ],
        text_format=PlantDiagnosis
    )

    result = response.output_parsed.model_dump()

    if not result.get("is_plant"):
        raise NonPlantImageError(result.get("non_plant_reason") or NON_PLANT_MESSAGE)

    diagnosis = result.get("diagnosis") if result.get("is_sick") else None
    real_links = search_disease_links(diagnosis)

    result["links"] = real_links
    result.pop("is_plant", None)
    result.pop("non_plant_reason", None)

    return result
