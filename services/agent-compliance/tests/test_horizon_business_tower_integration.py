"""Regression fixture for the building-type/height-aware topic bundles
(test/new/horizon input.pdf + hand-verified horizon expected output.pdf
at the repo root).

Deliberately a different building typology from the Meridian Logistics
Hub fixture (single-storey warehouse) — this one is a 14-storey, 42m
High-Rise office tower with a basement car park, exercising the
HIGH_RISE_TOPICS and BASEMENT_CAR_PARK_TOPICS bundles that the warehouse
fixture never touches.

Same conventions as the Meridian fixture: hits the real running stack
over HTTP, excluded from the default pytest run (see pytest.ini), run
explicitly with `pytest -m integration`.

Assertions are keyed by TOPIC POSITION, not by keyword-matching finding
text — checks are guaranteed to come back in the same order as
select_topics() (one per topic, per the AUDIT CHECKLIST contract), and
that's far more robust than searching finding text: the model correctly
cross-references related checks (e.g. the hydrant check legitimately
cites the vehicle-access table's 75% figure when reasoning about whether
access is "restricted"), so two genuinely different checks can share a
lot of vocabulary and defeat keyword-based disambiguation.
"""
import httpx
import pytest

from app.schemas import BuildingContext
from app.services.audit_topics import select_topics

COMPLIANCE_URL = "http://localhost:8002/api/v1/audit"

# Transcribed from test/new/horizon input.pdf at the repo root.
HORIZON_BUSINESS_TOWER = {
    "building_type": "14-storey office tower with ground floor lobby/retail and a basement car park",
    "occupancy_purpose_group": 3,  # Office
    "number_of_floors": 14,
    # Not mentioned anywhere in the input document. Set to False here
    # only because this fixture hand-types building_details directly
    # (bypassing intake) and the field used to be required; real intake
    # now correctly leaves this null when unstated (see Ironclad
    # Manufacturing Plant fixture in test/iteration_validation/).
    "has_extinguishers": False,
    "floor_area_sqm": 21000,  # total aggregate across all 14 storeys
    "height_m": 42,
    "has_sprinkler_system": True,
    "number_of_exits": 2,  # two protected internal staircases
    "has_external_hydrants": False,
    "has_fire_detection_alarm": True,
    "occupancy_hazard_classification": None,
    "has_basement_car_park": True,
    "has_stairway_pressurization": False,
    "has_smoke_control_system": False,
    "has_firemans_lift": True,
    "has_fire_fighting_shaft": True,
    "has_fire_command_centre": True,
    "has_voice_evacuation_system": False,
    "has_two_way_telephone_system": True,
    "number_of_wet_risers": 2,
    "has_refuge_floor": False,
    "has_evacuation_lift": False,
    "has_car_park_co_detection": True,
    "fire_engine_access_percentage": 40,
    "fire_pump_room_fire_resistance_minutes": None,
    "fire_pump_room_separation_m": None,
}


@pytest.mark.integration
def test_horizon_business_tower_audit_selects_high_rise_topics():
    response = httpx.post(
        COMPLIANCE_URL,
        json={"building_details": HORIZON_BUSINESS_TOWER},
        timeout=240.0,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    checks = body["detailed_checks"]

    # CORE + HIGH_RISE (42m > 30m) + BASEMENT_CAR_PARK — but NOT
    # STORAGE_INDUSTRIAL (Purpose Group 3, not 6/7) and NOT
    # SUPER_HIGH_RISE (42m, not > 60m). May be MORE than this if the
    # model found additional relevant Chapter 6 provisions to append.
    expected_topics = select_topics(BuildingContext(**HORIZON_BUSINESS_TOWER))
    assert len(checks) >= len(expected_topics)

    topic_ids = [topic_id for topic_id, _ in expected_topics]
    by_topic = dict(zip(topic_ids, checks))

    # refuge_floor/evacuation_lift must never have been selected at all —
    # this building is 42m, below the 60m Super-High-Rise threshold.
    assert "refuge_floor" not in by_topic
    assert "evacuation_lift" not in by_topic

    # This building has real violations (no pressurization, no smoke
    # control, no voice evacuation, only 40% vs required 75% fire engine
    # access) — must never be called COMPLIANT overall.
    assert body["overall_status"] == "NON_COMPLIANT"

    # Violations the high-rise bundle must catch (E1, E2, E7, E13).
    assert by_topic["stairway_pressurization"]["status"] == "NON_COMPLIANT"
    assert by_topic["smoke_control"]["status"] == "NON_COMPLIANT"
    assert by_topic["voice_evacuation"]["status"] == "NON_COMPLIANT"
    assert by_topic["fire_engine_access"]["status"] == "NON_COMPLIANT"

    # Correctly-provided high-rise systems must not be flagged as
    # violations (E3, E4, E8, E9, E10, E12).
    for topic_id in (
        "firemans_lift",
        "fire_fighting_shaft_fcc",
        "two_way_telephone",
        "wet_risers",
        "co_detection",
    ):
        assert by_topic[topic_id]["status"] != "NON_COMPLIANT", by_topic[topic_id]

    # Fire pump room: facts genuinely missing from the input — must ask,
    # not silently pass or fail.
    assert by_topic["fire_pump_room"]["status"] == "NEEDS_CLARIFICATION"
