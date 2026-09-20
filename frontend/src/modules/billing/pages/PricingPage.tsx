import { useState } from 'react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../../common/hooks/useAuth'
import { AppLayout } from '../../../common/layouts/AppLayout'
import { PLAN_CATALOG, PLAN_ORDER } from '../../../common/types/account'
import type { PlanId } from '../../../common/types/account'
import { UpgradeDialog } from '../../../common/components/UpgradeDialog'
import { CheckIcon, FlameIcon } from '../../../common/components/icons'
import { formatLkr } from '../../../common/utils/format'

const SALES_EMAIL = 'sales@fireguardai.app'
const SALES_LINK = `mailto:${SALES_EMAIL}?subject=${encodeURIComponent('Government plan inquiry')}`

const FEATURE_ROWS: { label: string; render: (plan: PlanId) => ReactNode }[] = [
  { label: 'Analysis input', render: (id) => PLAN_CATALOG[id].analysisInput },
  { label: 'Report limit', render: (id) => PLAN_CATALOG[id].reportLimitLabel },
  { label: 'Billing model', render: (id) => PLAN_CATALOG[id].billingLabel },
  {
    label: 'PDF plan analysis',
    render: (id) => (PLAN_CATALOG[id].features.pdfAnalysis ? <CheckIcon className="mx-auto h-4 w-4 text-emerald-600" /> : <span className="text-slate-300">—</span>),
  },
  {
    label: 'PDF report export',
    render: (id) => (PLAN_CATALOG[id].features.pdfAnalysis ? <CheckIcon className="mx-auto h-4 w-4 text-emerald-600" /> : <span className="text-slate-300">—</span>),
  },
  {
    label: 'External API access',
    render: (id) => (PLAN_CATALOG[id].features.externalApi ? <CheckIcon className="mx-auto h-4 w-4 text-emerald-600" /> : <span className="text-slate-300">—</span>),
  },
  {
    label: 'Institutional email required',
    render: (id) => (PLAN_CATALOG[id].requiresInstitutionalEmail ? <CheckIcon className="mx-auto h-4 w-4 text-emerald-600" /> : <span className="text-slate-300">—</span>),
  },
]

function PricingTable({ upgradeTarget, setUpgradeTarget }: { upgradeTarget: PlanId | null; setUpgradeTarget: (plan: PlanId | null) => void }) {
  const { account, isAuthenticated } = useAuth()

  function cta(id: PlanId) {
    const definition = PLAN_CATALOG[id]
    if (!isAuthenticated) {
      if (id === 'government') {
        return (
          <a href={SALES_LINK} className="block w-full rounded-lg bg-slate-900 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-slate-800">
            Talk to sales
          </a>
        )
      }
      return (
        <Link
          to={`/register?plan=${id}`}
          className="block w-full rounded-lg bg-orange-500 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-orange-600"
        >
          {id === 'student' ? 'Get started free' : `Choose ${definition.name}`}
        </Link>
      )
    }

    if (account?.plan === id) {
      return (
        <button type="button" disabled className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-400">
          Current plan
        </button>
      )
    }
    if (id === 'government') {
      return (
        <a href={SALES_LINK} className="block w-full rounded-lg bg-slate-900 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-slate-800">
          Talk to sales
        </a>
      )
    }
    if (id === 'student') {
      return (
        <button
          type="button"
          disabled
          title="Contact support to switch back to the Student plan."
          className="w-full rounded-lg border border-dashed border-slate-200 px-3 py-2 text-sm font-medium text-slate-400"
        >
          Contact support
        </button>
      )
    }
    return (
      <button
        type="button"
        onClick={() => setUpgradeTarget(id)}
        className="w-full rounded-lg bg-orange-500 px-3 py-2 text-sm font-semibold text-white hover:bg-orange-600"
      >
        Choose {definition.name}
      </button>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] border-collapse text-sm">
        <thead>
          <tr>
            <th className="w-40 pb-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">Compare plans</th>
            {PLAN_ORDER.map((id) => (
              <th key={id} className="border-l border-slate-100 px-4 pb-4 text-left align-top">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-900">{PLAN_CATALOG[id].name}</span>
                  {account?.plan === id && (
                    <span className="rounded-full bg-slate-900 px-2 py-0.5 text-[10px] font-semibold uppercase text-white">Current</span>
                  )}
                </div>
                <p className="mt-2 text-xl font-semibold text-slate-900">
                  {PLAN_CATALOG[id].mockAmount === null
                    ? PLAN_CATALOG[id].billingModel === 'contact-sales'
                      ? 'Custom'
                      : 'Free'
                    : formatLkr(PLAN_CATALOG[id].mockAmount)}
                </p>
                <p className="text-xs text-slate-400">
                  {PLAN_CATALOG[id].billingModel === 'per-report'
                    ? 'per report credit'
                    : PLAN_CATALOG[id].billingModel === 'subscription'
                      ? 'per month'
                      : PLAN_CATALOG[id].billingModel === 'contact-sales'
                        ? 'annual agreement'
                        : 'with verified institutional email'}
                </p>
                <p className="mt-1 text-xs text-slate-500">{PLAN_CATALOG[id].tagline}</p>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {FEATURE_ROWS.map((row) => (
            <tr key={row.label}>
              <td className="py-3 pr-4 text-slate-500">{row.label}</td>
              {PLAN_ORDER.map((id) => (
                <td key={id} className="border-l border-slate-100 px-4 py-3 text-slate-800">
                  {row.render(id)}
                </td>
              ))}
            </tr>
          ))}
          <tr>
            <td className="pt-4" />
            {PLAN_ORDER.map((id) => (
              <td key={id} className="border-l border-slate-100 px-4 pt-4">
                {cta(id)}
              </td>
            ))}
          </tr>
        </tbody>
      </table>

      <p className="mt-6 text-xs text-slate-400">
        Student plans require a verified institutional email (e.g. @sliit.lk, @uom.lk) and are limited to five
        text-based reports each month. Government agreements are provisioned by our billing team, not through
        self-serve checkout.
      </p>

      {upgradeTarget && <UpgradeDialog plan={upgradeTarget} onClose={() => setUpgradeTarget(null)} />}
    </div>
  )
}

function PricingPage() {
  const { isAuthenticated } = useAuth()
  const [upgradeTarget, setUpgradeTarget] = useState<PlanId | null>(null)

  const header = (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Plans</p>
      <h1 className="mt-1 text-2xl font-semibold text-slate-900">Choose how you audit</h1>
      <p className="mt-1 text-sm text-slate-500">
        Every plan runs the same four-agent pipeline and cites the same regulation index. Plans differ in input
        type, volume and automation.
      </p>
    </div>
  )

  if (isAuthenticated) {
    return (
      <AppLayout>
        {header}
        <div className="mt-6">
          <PricingTable upgradeTarget={upgradeTarget} setUpgradeTarget={setUpgradeTarget} />
        </div>
      </AppLayout>
    )
  }

  return (
    <div className="min-h-screen bg-white px-6 py-10">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center justify-between">
          <Link to="/login" className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500 text-white">
              <FlameIcon className="h-4.5 w-4.5" />
            </span>
            <span className="text-base font-semibold text-slate-900">
              FireGuard<span className="text-orange-500">AI</span>
            </span>
          </Link>
          <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900">
            Sign in
          </Link>
        </div>

        <div className="mt-8">{header}</div>
        <div className="mt-6">
          <PricingTable upgradeTarget={upgradeTarget} setUpgradeTarget={setUpgradeTarget} />
        </div>
      </div>
    </div>
  )
}

export default PricingPage
