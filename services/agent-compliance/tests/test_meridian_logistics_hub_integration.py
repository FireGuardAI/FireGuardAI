"""Regression fixture for the accuracy investigation in test/ at the repo
root (Meridian Logistics Hub building description + hand-verified
Expected output.pdf answer key).

This hits the REAL, already-running stack (agent-compliance ->
agent-retrieval -> Gemini) over HTTP, not an in-process mock — it needs
`docker compose up` for agent-compliance and agent-retrieval, and a real
GEMINI_API_KEY configured on the running agent-compliance container.
Excluded from the default `pytest` run (see pytest.ini); run explicitly
with `pytest -m integration`.

LLM output isn't byte-reproducible, so assertions check structural
properties (status directions, checklist completeness) rather than exact
wording — the goal is to catch a regression back to the old behavior
(everything either silently missing or downgraded to INSUFFICIENT_DATA),
not to pin the model's phrasing.
"""
import httpx
import pytest

from app.schemas import BuildingContext
from app.services.audit_topics import select_topics

COMPLIANCE_URL = "http://localhost:8002/api/v1/audit"

# Transcribed from test/input document.pdf at the repo root.
MERIDIAN_LOGISTICS_HUB = {
    "building_type": "single-storey warehouse for general goods storage (Purpose Group 7(b))",
    "occupancy_purpose_group": 7,
    "number_of_floors": 1,
    "has_extinguishers": True,
    "extinguisher_details": (
        "Dry powder, Class A/B rated extinguishers wall-mounted on columns "
        "along the main aisle at approximately 45 m intervals"
    ),
    "floor_area_sqm": 9000,
    "height_m": 20,
    "occupant_load": 120,
    "has_sprinkler_system": False,
    "number_of_exits": 1,
    "min_exit_width_mm": 1200,
    "max_travel_distance_m": 65,
    "dead_end_corridor_length_m": 25,
    "has_hose_reels": False,
    "has_external_hydrants": False,
    "has_fire_detection_alarm": False,
    "structural_fire_resistance_minutes": 90,
    # Deliberately omitted, matching the input document: the auditor's
    # note (6 m high racking, 1.5 m roof clearance) hints at a hazard
    # class but never states one — this is exactly what the Expected
    # output.pdf's NEEDS_CLARIFICATION item is about.
    "occupancy_hazard_classification": None,
}


@pytest.mark.integration
def test_meridian_logistics_hub_audit_flags_real_violations():
    response = httpx.post(
        COMPLIANCE_URL,
        json={"building_details": MERIDIAN_LOGISTICS_HUB},
        timeout=240.0,
    )
    assert response.status_code == 200, response.text
    body = response.json()

    checks = body["detailed_checks"]

    # Checklist-driven auditing: the first len(expected_topics) checks
    # come back one per selected topic, in order — this building is
    # single-storey/20m (below the 30m High-Rise threshold) storage
    # (Purpose Group 7) with no basement car park, so CORE +
    # STORAGE_INDUSTRIAL only. There may be MORE than this: the
    # generalized fix lets the model append additional checks it finds
    # in the Chapter 6 occupancy-specific content, so this is a floor,
    # not an exact count.
    expected_topics = select_topics(BuildingContext(**MERIDIAN_LOGISTICS_HUB))
    assert len(checks) >= len(expected_topics)

    # Phase 4: this building has real violations (no sprinkler at 20m
    # with combustible storage, single exit, 65m travel distance, 25m
    # dead-end corridor, 45m > 30m extinguisher spacing, no detection/
    # alarm, no hose reel, no hydrant) — the deterministic scorer must
    # never call this COMPLIANT.
    assert body["overall_status"] == "NON_COMPLIANT"

    findings_text = " ".join(f"{c['rule_clause']} {c['finding']}".lower() for c in checks)

    # At least the sprinkler and extinguisher-spacing topics — both of
    # which the pre-fix pipeline missed or downgraded to
    # INSUFFICIENT_DATA — must land on a genuine violation now that the
    # facts reach compliance and multi-topic retrieval can find Reg
    # 3(20)/5(33) and Reg 5(4).
    non_compliant_findings = " ".join(
        f"{c['rule_clause']} {c['finding']}".lower()
        for c in checks
        if c["status"] == "NON_COMPLIANT"
    )
    assert "sprinkler" in non_compliant_findings, findings_text
    assert any(kw in non_compliant_findings for kw in ("extinguish", "45 m", "45m")), findings_text

    # The hazard-classification topic must not be silently marked
    # COMPLIANT — the input never stated a classification.
    hazard_checks = [c for c in checks if "hazard" in c["rule_clause"].lower() or "hazard" in c["finding"].lower()]
    assert hazard_checks, "expected a hazard-classification check in the fixed checklist"
    assert all(c["status"] != "COMPLIANT" for c in hazard_checks)
