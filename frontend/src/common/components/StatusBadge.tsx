import { AlertTriangleIcon, CheckCircleIcon, SearchIcon, XCircleIcon } from './icons'

// Covers both RuleStatus (per-check) and OverallStatus (building-level)
// values in one map, since this badge renders both. Falls back to the
// UNKNOWN entry for anything not listed here rather than silently
// reusing another status's label.
const STYLES: Record<string, { label: string; className: string; Icon: typeof CheckCircleIcon }> = {
  COMPLIANT: {
    label: 'Compliant',
    className: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
    Icon: CheckCircleIcon,
  },
  PARTIAL: {
    label: 'Partial',
    className: 'bg-amber-50 text-amber-700 ring-amber-600/20',
    Icon: AlertTriangleIcon,
  },
  NON_COMPLIANT: {
    label: 'Non-compliant',
    className: 'bg-red-50 text-red-600 ring-red-600/20',
    Icon: XCircleIcon,
  },
  INSUFFICIENT_DATA: {
    label: 'Insufficient data',
    className: 'bg-slate-100 text-slate-600 ring-slate-500/20',
    Icon: AlertTriangleIcon,
  },
  // A check whose regulation text was found but the building description
  // omitted a needed fact — a question for the building owner, not a
  // missing document, so it gets its own look rather than sharing
  // INSUFFICIENT_DATA's "pipeline gap" styling.
  NEEDS_CLARIFICATION: {
    label: 'Needs clarification',
    className: 'bg-sky-50 text-sky-700 ring-sky-600/20',
    Icon: SearchIcon,
  },
  // The requirement genuinely doesn't apply to this building (e.g. a
  // refuge floor rule on a building under the height threshold) — the
  // absence is correct, not a violation, so it must not read as a failure.
  NOT_APPLICABLE: {
    label: 'Not applicable',
    className: 'bg-slate-50 text-slate-400 ring-slate-300/40',
    Icon: CheckCircleIcon,
  },
  // Overall-status only: no confirmed violation, but one or more checks
  // are unresolved. Must never read as compliant (green) or as a generic
  // "insufficient data" pipeline issue — it's an open, unresolved audit.
  NEEDS_REVIEW: {
    label: 'Needs review',
    className: 'bg-orange-50 text-orange-700 ring-orange-600/20',
    Icon: AlertTriangleIcon,
  },
}

const UNKNOWN_STYLE = { label: 'Unknown', className: 'bg-slate-100 text-slate-600 ring-slate-500/20', Icon: AlertTriangleIcon }

export function StatusBadge({ status, className = '' }: { status: string; className?: string }) {
  const { label, className: styleClassName, Icon } = STYLES[status.toUpperCase()] ?? UNKNOWN_STYLE
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${styleClassName} ${className}`}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </span>
  )
}
