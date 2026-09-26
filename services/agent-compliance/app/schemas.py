from typing import Literal, Optional

from pydantic import BaseModel, Field


class BuildingContext(BaseModel):
    building_type: str = Field(
        ..., description="e.g., Commercial, Residential, Hospital, Warehouse/Storage"
    )
    # Confidently inferred by intake (like building_type), never left null —
    # see the note in fireguard-agent-intake's prompt for why this is
    # exempt from the "never guess" rule that applies to every other field
    # here. Drives which audit-topic bundles apply (see audit_topics.py).
    occupancy_purpose_group: int = Field(..., ge=1, le=8)
    # Confidently inferred, like occupancy_purpose_group — a building
    # actively being built is governed by an entirely different,
    # self-contained set of provisions (Reg. 5(31), Reg. 4(27)-4(28)),
    # not the full occupied-building checklist. Defaults to "completed"
    # because that's the overwhelmingly common case and nothing in a
    # normal building description would ever mention construction phase.
    construction_status: Literal["completed", "under_construction"] = "completed"
    number_of_floors: int = Field(..., gt=0)
    # Was required (non-nullable) — that forced intake to guess False
    # whenever an input simply never mentioned extinguishers, silently
    # fabricating a violation. Nullable like every other safety-critical
    # fact; a null here means "not stated", handled correctly by the
    # existing null-handling rule in the compliance prompt with no
    # extinguisher-specific logic needed.
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


CheckStatus = Literal[
    "COMPLIANT",
    "NON_COMPLIANT",
    "PARTIAL",
    "INSUFFICIENT_DATA",
    "NEEDS_CLARIFICATION",
    "NOT_APPLICABLE",
]

OverallStatus = Literal["COMPLIANT", "NON_COMPLIANT", "NEEDS_REVIEW"]


class ComplianceRuleCheck(BaseModel):
    rule_clause: str = Field(..., description="e.g., Reg.5(2)(a)")
    status: CheckStatus = Field(
        ...,
        description=(
            "COMPLIANT/NON_COMPLIANT/PARTIAL: verdict reached from the retrieved "
            "regulation text. INSUFFICIENT_DATA: the regulation text needed to "
            "evaluate this topic wasn't found in the retrieved context. "
            "NEEDS_CLARIFICATION: the retrieved regulation text was found, but the "
            "building description itself didn't state a fact a competent auditor "
            "would need to ask about. NOT_APPLICABLE: the requirement genuinely "
            "does not apply to this building given its stated facts (e.g. a "
            "refuge floor is only required above 60m and this building is 42m) — "
            "the system's absence is correct, not a violation."
        ),
    )
    finding: str
    recommendation: Optional[str] = None


class ComplianceAssessment(BaseModel):
    """What Gemini actually produces — one check per audit topic plus a
    narrative summary. overall_status/compliance_score are deliberately
    NOT part of this model: they're computed deterministically in code
    from detailed_checks (see main.py's _score_audit), never left to the
    model's own judgment call."""

    detailed_checks: list[ComplianceRuleCheck]
    summary: str


class ComplianceResponse(BaseModel):
    overall_status: OverallStatus
    compliance_score: float = Field(..., ge=0.0, le=100.0)
    detailed_checks: list[ComplianceRuleCheck]
    summary: str


class AuditRequest(BaseModel):
    building_details: BuildingContext
    # The original, un-decomposed building description, if available.
    # SanitizedBuildingDetails/BuildingContext will never cover every
    # fact for every occupancy type — this lets the compliance LLM
    # cross-reference facts the structured schema has no field for yet,
    # instead of treating them as unknown.
    raw_description: Optional[str] = None
