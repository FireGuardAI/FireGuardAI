from typing import Literal, Optional

from pydantic import BaseModel, Field

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
    status: CheckStatus
    finding: str
    recommendation: Optional[str] = None


class ComplianceResponse(BaseModel):
    audit_id: str
    overall_status: OverallStatus
    compliance_score: float = Field(..., ge=0.0, le=100.0)
    detailed_checks: list[ComplianceRuleCheck]
    summary: str
    executive_summary_markdown: Optional[str] = None
    report_generated_by: Optional[str] = None
    loop_turns_used: int
    tool_calls_used: int
    terminated_by: Literal["model_submitted", "budget_exhausted"]


class AuditRequest(BaseModel):
    # Same input shape as the old /api/v1/audit — either already-extracted
    # building_details (skips the EXTRACT step) or raw text/PDF for the
    # loop to extract itself via the intake MCP tool.
    building_details: Optional[dict] = None
    raw_description: Optional[str] = None
    raw_text: Optional[str] = None
