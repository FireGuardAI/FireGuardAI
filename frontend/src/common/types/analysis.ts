// Matches the status vocabulary used by fireguard-agent-compliance's ComplianceRuleCheck.
export type RuleStatus = 'COMPLIANT' | 'NON_COMPLIANT' | 'PARTIAL' | 'INSUFFICIENT_DATA'

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
