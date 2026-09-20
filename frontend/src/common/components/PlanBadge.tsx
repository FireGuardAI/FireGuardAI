import { PLAN_CATALOG } from '../types/account'
import type { PlanId } from '../types/account'

export function PlanBadge({ plan, className = '' }: { plan: PlanId; className?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border border-sky-200 bg-sky-50 px-2.5 py-0.5 text-xs font-medium text-sky-700 ${className}`}
    >
      {PLAN_CATALOG[plan].name}
    </span>
  )
}
