from pydantic import BaseModel
from typing import List, Optional


class PlantDiagnosis(BaseModel):
    is_plant: bool
    is_sick: bool
    diagnosis: Optional[str]
    description: str
    characteristics: List[str]
    treatment_steps: List[str]
    links: List[str]
    confidence: float
    message: str