import { apiRequest } from './api'
import type { AnalysisMode, AnalysisReport, RuleCheckItem, RuleStatus } from '../types/analysis'

const KNOWN_STATUSES: RuleStatus[] = ['COMPLIANT', 'NON_COMPLIANT', 'PARTIAL', 'INSUFFICIENT_DATA']

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {}
}

function asStatus(value: unknown): RuleStatus {
  const upper = typeof value === 'string' ? value.toUpperCase() : ''
  return (KNOWN_STATUSES as string[]).includes(upper) ? (upper as RuleStatus) : 'INSUFFICIENT_DATA'
}

// The gateway's /analyze and /analyze/text responses ultimately depend on
// fireguard-agent-compliance's ComplianceResponse and fireguard-agent-report's
// ReportResponse — two contracts that aren't joined into one documented shape yet.
// This normalizes whatever comes back (possibly wrapped in a "report" envelope)
// into a single AnalysisReport instead of assuming a specific shape.
function normalizeReport(raw: unknown, fallbackName: string, mode: AnalysisMode): AnalysisReport {
  const data = asRecord(raw)
  const nested = 'report' in data ? asRecord(data.report) : data

  const rawChecks = Array.isArray(nested.detailed_checks) ? nested.detailed_checks : []
  const detailedChecks: RuleCheckItem[] = rawChecks.map((entry) => {
    const check = asRecord(entry)
    return {
      rule_clause: typeof check.rule_clause === 'string' ? check.rule_clause : 'Unlabeled clause',
      status: asStatus(check.status),
      finding: typeof check.finding === 'string' ? check.finding : '',
      recommendation: typeof check.recommendation === 'string' ? check.recommendation : null,
    }
  })

  return {
    id: crypto.randomUUID(),
    buildingName: typeof nested.building_name === 'string' ? nested.building_name : fallbackName,
    mode,
    submittedAt: new Date().toISOString(),
    overallStatus: typeof nested.overall_status === 'string' ? nested.overall_status : 'INSUFFICIENT_DATA',
    complianceScore: typeof nested.compliance_score === 'number' ? nested.compliance_score : null,
    summary: typeof nested.summary === 'string' ? nested.summary : null,
    executiveSummaryMarkdown:
      typeof nested.executive_summary_markdown === 'string' ? nested.executive_summary_markdown : null,
    generatedBy: typeof nested.generated_by === 'string' ? nested.generated_by : null,
    detailedChecks,
  }
}

export interface TextAnalysisInput {
  rawPrompt: string
  buildingName?: string
  auditorNotes?: string
}

export async function submitTextAnalysis(token: string, input: TextAnalysisInput): Promise<AnalysisReport> {
  const raw = await apiRequest<unknown>('/analyze/text', {
    method: 'POST',
    token,
    body: JSON.stringify({
      raw_prompt: input.rawPrompt,
      building_name: input.buildingName,
      auditor_notes: input.auditorNotes,
    }),
  })
  return normalizeReport(raw, input.buildingName ?? 'Untitled building', 'text')
}

export async function submitPdfAnalysis(
  token: string,
  file: File,
  buildingName?: string,
  auditorNotes?: string,
): Promise<AnalysisReport> {
  const form = new FormData()
  form.append('file', file)
  if (buildingName) form.append('building_name', buildingName)
  if (auditorNotes) form.append('auditor_notes', auditorNotes)

  const raw = await apiRequest<unknown>('/analyze', { method: 'POST', token, body: form })
  return normalizeReport(raw, buildingName ?? file.name, 'pdf')
}

// There is no backend endpoint yet for listing a user's past reports, so completed
// analyses are kept client-side, namespaced per account id.
const HISTORY_KEY_PREFIX = 'fireguard.analysis-history.'

export function listAnalysisRecords(userId: string): AnalysisReport[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY_PREFIX + userId)
    return raw ? (JSON.parse(raw) as AnalysisReport[]) : []
  } catch {
    return []
  }
}

export function saveAnalysisRecord(userId: string, report: AnalysisReport): void {
  const next = [report, ...listAnalysisRecords(userId)].slice(0, 25)
  localStorage.setItem(HISTORY_KEY_PREFIX + userId, JSON.stringify(next))
}

export function getAnalysisRecord(userId: string, id: string): AnalysisReport | undefined {
  return listAnalysisRecords(userId).find((record) => record.id === id)
}
