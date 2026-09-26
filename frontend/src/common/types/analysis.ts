// Matches the status vocabulary used by fireguard-agent-compliance's (and
// fireguard-agent-orchestrator's) ComplianceRuleCheck. NEEDS_CLARIFICATION and
// NOT_APPLICABLE carry distinct meanings from INSUFFICIENT_DATA — see the
// backend's REPORT_GENERATION_PROMPT — so they must not collapse into it here.
export type RuleStatus =
  | 'COMPLIANT'
  | 'NON_COMPLIANT'
  | 'PARTIAL'
  | 'INSUFFICIENT_DATA'
  | 'NEEDS_CLARIFICATION'
  | 'NOT_APPLICABLE'

// The building-level verdict — a distinct, smaller vocabulary from RuleStatus.
// NEEDS_REVIEW must never be rendered as compliant or as "insufficient data":
// it means no confirmed violation exists, but the audit is open/unresolved.
export type OverallStatus = 'COMPLIANT' | 'NON_COMPLIANT' | 'NEEDS_REVIEW'

export interface RuleCheckItem {
  rule_clause: string
  status: RuleStatus
  finding: string
  recommendation: string | null
}

export type AnalysisMode = 'text' | 'pdf'

// The gateway's /analyze and /analyze/text responses depend on downstream agents
// (fireguard-agent-compliance's ComplianceResponse and fireguard-agent-report's
// ReportResponse) that aren't fully wired end-to-end yet, so every field here is
// optional and normalized defensively in analysisService.ts.
export interface AnalysisReport {
  id: string
  buildingName: string
  mode: AnalysisMode
  submittedAt: string
  overallStatus: string
  complianceScore: number | null
  summary: string | null
  executiveSummaryMarkdown: string | null
  generatedBy: string | null
  detailedChecks: RuleCheckItem[]
}
