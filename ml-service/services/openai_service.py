import base64
import os

from dotenv import load_dotenv
from openai import OpenAI

from models.diagnosis_schema import PlantDiagnosis
from services.web_search_service import search_disease_links

load_dotenv()


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required to analyze plant images.")

    return OpenAI(api_key=api_key)


def analyze_plant_image(image_bytes, prompt_text):
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
                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    }
                ]
            }
        ],
        text_format=PlantDiagnosis
    )

    result = response.output_parsed.model_dump()

    diagnosis = result.get("diagnosis")

    real_links = search_disease_links(diagnosis)

    result["links"] = real_links

    return result
