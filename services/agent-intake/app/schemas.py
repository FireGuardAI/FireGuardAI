"""Pydantic request/response models for the intake API."""
from typing import Optional

from pydantic import BaseModel, Field


class RawBuildingInput(BaseModel):
    raw_prompt: str = Field(
        ...,
        min_length=1,
        description="e.g. I have a 5-story commercial space with 5kg "
        "ABC extinguishers on each floor.",
    )


class SanitizedBuildingDetails(BaseModel):
    is_fire_safety_related: bool
    is_safe_input: bool
    building_type: str
    number_of_floors: int
    has_extinguishers: bool
    extinguisher_details: Optional[str] = None
    sanitization_notes: Optional[str] = None
