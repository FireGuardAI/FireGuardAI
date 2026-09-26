"""Pydantic request/response models for the intake API."""
from typing import Literal, Optional

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
    # Like building_type, this is confidently inferred, not left null when
    # unstated — it's a categorization task (unambiguous from context: an
    # "office building" is obviously 3, a "warehouse" is obviously 7), not
    # a fact about an installed system where a wrong guess could hide or
    # invent a violation. Leaving it null-by-default would silently
    # disable topic-bundle gating in compliance for most real inputs,
    # since descriptions almost never state "Purpose Group N" explicitly.
    occupancy_purpose_group: int
    # Confidently inferred, like occupancy_purpose_group — defaults to
    # "completed" (the overwhelming majority of real inputs) unless the
    # description clearly states the building is actively being built,
    # e.g. "under construction", "structural work complete up to floor
    # N", "temporary fire pump". Governs whether compliance applies the
    # occupied-building checklist or the separate construction-phase one.
    construction_status: Literal["completed", "under_construction"] = "completed"
    number_of_floors: int
    # Was required (defaulting False whenever unstated) — that silently
    # fabricated a "no extinguishers installed" violation on any input
    # that simply never mentions them (confirmed on the Ironclad
    # Manufacturing Plant fixture, which never mentions extinguishers at
    # all). Nullable like every other safety-critical fact now: a null
    # here means "not stated", not "confirmed absent", and the
    # compliance prompt's existing null-handling rule (never assume a
    # null field is compliant or non-compliant) covers it correctly
    # without any extinguisher-specific logic.
    has_extinguishers: Optional[bool] = None
    extinguisher_details: Optional[str] = None
    floor_area_sqm: Optional[float] = None
    height_m: Optional[float] = None
    occupant_load: Optional[int] = None
    has_sprinkler_system: Optional[bool] = None
    number_of_exits: Optional[int] = None
    min_exit_width_mm: Optional[int] = None
    max_travel_distance_m: Optional[float] = None
    dead_end_corridor_length_m: Optional[float] = None
    has_hose_reels: Optional[bool] = None
    has_external_hydrants: Optional[bool] = None
    has_fire_detection_alarm: Optional[bool] = None
    structural_fire_resistance_minutes: Optional[int] = None
    occupancy_hazard_classification: Optional[str] = None
    has_basement_car_park: Optional[bool] = None
    has_stairway_pressurization: Optional[bool] = None
    has_smoke_control_system: Optional[bool] = None
    has_firemans_lift: Optional[bool] = None
    has_fire_fighting_shaft: Optional[bool] = None
    has_fire_command_centre: Optional[bool] = None
    has_voice_evacuation_system: Optional[bool] = None
    has_two_way_telephone_system: Optional[bool] = None
    number_of_wet_risers: Optional[int] = None
    has_refuge_floor: Optional[bool] = None
    has_evacuation_lift: Optional[bool] = None
    has_car_park_co_detection: Optional[bool] = None
    fire_engine_access_percentage: Optional[float] = None
    fire_pump_room_fire_resistance_minutes: Optional[int] = None
    fire_pump_room_separation_m: Optional[float] = None
    sanitization_notes: Optional[str] = None
    # Attached by the route after parsing, NOT produced by the LLM (never
    # part of its JSON schema/prompt) — the verbatim raw_prompt or
    # PDF-extracted text, so compliance can cross-reference facts this
    # schema has no field for yet instead of losing them after intake.
    # Defaults to "" so LLM-driven construction (`SanitizedBuildingDetails(**parsed)`)
    # never fails on a missing key.
    raw_description: str = ""
