"""Deterministic overall_status/compliance_score from the individual
check verdicts — ported unchanged from fireguard-agent-compliance's
_score_audit. This is the one piece of the old pipeline the agentic loop
explicitly does NOT change: the LLM never grades itself, because letting
it self-report a score previously produced contradictory results (e.g.
100% "compliant" with more unresolved gaps than a separate run that
scored 50% "non-compliant" for the same building). The agent loop only
ever produces `detailed_checks`; this function is the only thing allowed
to compute overall_status/compliance_score from them."""
from app.schemas import ComplianceRuleCheck, OverallStatus


def score_audit(checks: list[ComplianceRuleCheck]) -> tuple[OverallStatus, float]:
    # NOT_APPLICABLE checks are excluded from both sides of the ratio — a
    # building shouldn't score higher just because more of its checklist
    # happened not to apply to it.
    scored = [c for c in checks if c.status != "NOT_APPLICABLE"]
    compliant = sum(c.status == "COMPLIANT" for c in scored)
    non_compliant = sum(c.status == "NON_COMPLIANT" for c in scored)
    partial = sum(c.status == "PARTIAL" for c in scored)
    total = len(scored) or 1
    score = round(100 * (compliant + 0.5 * partial) / total, 1)

    if non_compliant:
        status: OverallStatus = "NON_COMPLIANT"
    elif any(c.status in ("INSUFFICIENT_DATA", "NEEDS_CLARIFICATION") for c in checks):
        status = "NEEDS_REVIEW"
    else:
        status = "COMPLIANT"
    return status, score
