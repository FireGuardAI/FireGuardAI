import type { RuleStatus } from '../types/analysis'
import { AlertTriangleIcon, CheckCircleIcon, XCircleIcon } from './icons'

const STYLES: Record<RuleStatus, { label: string; className: string; Icon: typeof CheckCircleIcon }> = {
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
}

export function StatusBadge({ status, className = '' }: { status: string; className?: string }) {
  const normalized = (status.toUpperCase() as RuleStatus) in STYLES ? (status.toUpperCase() as RuleStatus) : 'INSUFFICIENT_DATA'
  const { label, className: styleClassName, Icon } = STYLES[normalized]
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${styleClassName} ${className}`}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </span>
  )
}
