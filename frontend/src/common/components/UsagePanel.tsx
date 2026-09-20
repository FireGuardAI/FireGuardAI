import { Link } from 'react-router-dom'
import type { AccountResponse } from '../types/account'
import { PLAN_CATALOG } from '../types/account'
import { UsageMeter } from './UsageMeter'
import { CheckCircleIcon } from './icons'

const STUDENT_MONTHLY_LIMIT = 5

export function UsagePanel({ account }: { account: AccountResponse }) {
  const plan = PLAN_CATALOG[account.plan]

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Usage this month</p>
        <span className="inline-flex items-center rounded-full border border-sky-200 bg-sky-50 px-2 py-0.5 text-xs font-medium text-sky-700">
          {plan.name}
        </span>
      </div>
      <div className="mt-3">
        {account.plan === 'student' ? (
          <UsageMeter used={account.reports_used_this_month} limit={STUDENT_MONTHLY_LIMIT} />
        ) : account.plan === 'basic' ? (
          <div>
            <p className="text-2xl font-semibold text-slate-900">{account.reports_remaining ?? 0}</p>
            <p className="text-sm text-slate-500">report credits remaining</p>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <CheckCircleIcon className="h-4.5 w-4.5 text-emerald-500" />
            Unlimited reports on {plan.name}
          </div>
        )}
      </div>
      <Link to="/account/billing" className="mt-3 inline-block text-xs font-medium text-orange-600 hover:text-orange-700">
        Manage plan
      </Link>
    </div>
  )
}
