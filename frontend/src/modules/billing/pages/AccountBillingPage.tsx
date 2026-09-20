import { useState } from 'react'
import { useAuth } from '../../../common/hooks/useAuth'
import { UsagePanel } from '../../../common/components/UsagePanel'
import { LockedFeatureRow } from '../../../common/components/LockedFeatureCard'
import { UpgradeDialog } from '../../../common/components/UpgradeDialog'
import { PLAN_CATALOG, PLAN_ORDER } from '../../../common/types/account'
import type { PlanId } from '../../../common/types/account'
import { formatLkr } from '../../../common/utils/format'
import { FileTextIcon } from '../../../common/components/icons'

const SALES_LINK = `mailto:sales@fireguardai.app?subject=${encodeURIComponent('Jurisdiction-wide access inquiry')}`

function nextPlan(current: PlanId): PlanId | null {
  const index = PLAN_ORDER.indexOf(current)
  return index >= 0 && index < PLAN_ORDER.length - 1 ? PLAN_ORDER[index + 1] : null
}

function AccountBillingPage() {
  const { account } = useAuth()
  const [upgradeTarget, setUpgradeTarget] = useState<PlanId | null>(null)

  if (!account) return null
  const plan = PLAN_CATALOG[account.plan]
  const upsellTarget = nextPlan(account.plan)

  return (
    <div>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Account</p>
          <h1 className="mt-1 text-2xl font-semibold text-slate-900">Account & billing</h1>
          <p className="mt-1 text-sm text-slate-500">Your plan, what it unlocks, and how much of it you have used.</p>
        </div>
        {upsellTarget &&
          (upsellTarget === 'government' ? (
            <a
              href={SALES_LINK}
              className="self-start rounded-lg bg-orange-500 px-4 py-2 text-sm font-semibold text-white hover:bg-orange-600"
            >
              Talk to sales
            </a>
          ) : (
            <button
              type="button"
              onClick={() => setUpgradeTarget(upsellTarget)}
              className="self-start rounded-lg bg-orange-500 px-4 py-2 text-sm font-semibold text-white hover:bg-orange-600"
            >
              Upgrade to {PLAN_CATALOG[upsellTarget].name}
            </button>
          ))}
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <p className="text-sm font-semibold text-slate-900">Current plan</p>
                <span className="inline-flex items-center rounded-full border border-sky-200 bg-sky-50 px-2 py-0.5 text-xs font-medium text-sky-700">
                  {plan.name}
                </span>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold text-slate-900">
                  {plan.mockAmount === null ? (plan.billingModel === 'contact-sales' ? 'Custom' : 'Free') : formatLkr(plan.mockAmount)}
                </p>
                {plan.requiresInstitutionalEmail && <p className="text-xs text-slate-400">with verified institutional email</p>}
              </div>
            </div>
            <p className="mt-1 text-sm text-slate-500">{plan.tagline}</p>

            <div className="mt-4 grid grid-cols-1 gap-4 border-t border-slate-100 pt-4 sm:grid-cols-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Analysis input</p>
                <p className="mt-1 text-sm text-slate-800">{plan.analysisInput}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Report limit</p>
                <p className="mt-1 text-sm text-slate-800">{plan.reportLimitLabel}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Billing</p>
                <p className="mt-1 text-sm text-slate-800">{plan.billingLabel}</p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm font-semibold text-slate-900">Feature entitlements</p>
            <p className="text-sm text-slate-500">What is active on {plan.name} today.</p>
            <div className="mt-2 divide-y divide-slate-100">
              <LockedFeatureRow
                title="Building plan (PDF) analysis"
                availableOn="Basic, Pro, Enterprise, Government"
                unlocked={plan.features.pdfAnalysis}
              />
              <LockedFeatureRow
                title="PDF report export"
                availableOn="Basic, Pro, Enterprise, Government"
                unlocked={plan.features.pdfAnalysis}
              />
              <LockedFeatureRow
                title="External API access"
                availableOn="Enterprise, Government"
                unlocked={plan.features.externalApi}
              />
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm font-semibold text-slate-900">Invoices</p>
            <div className="mt-4 flex flex-col items-center gap-1 py-8 text-center">
              <FileTextIcon className="h-6 w-6 text-slate-300" />
              <p className="text-sm font-medium text-slate-700">No invoices yet</p>
              <p className="max-w-sm text-sm text-slate-500">
                {plan.billingModel === 'free'
                  ? 'Student accounts are free while your institutional email stays verified.'
                  : 'Invoice history is generated by billing and is not available in this preview yet.'}
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <UsagePanel account={account} />

          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Payment method</p>
            <p className="mt-2 text-sm text-slate-500">None on file. Payments in this environment are mocked.</p>
            <button
              type="button"
              disabled
              title="Payment processing is mocked in this environment."
              className="mt-3 w-full cursor-not-allowed rounded-md border border-slate-200 px-3 py-2 text-sm font-medium text-slate-400"
            >
              Update payment method
            </button>
          </div>

          {account.plan !== 'government' && (
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-5 text-white">
              <p className="text-sm font-semibold">Need jurisdiction-wide access?</p>
              <p className="mt-1 text-sm text-slate-300">
                Government plans add unlimited reports and API access under one agreement.
              </p>
              <a
                href={SALES_LINK}
                className="mt-3 inline-flex w-full items-center justify-center rounded-md bg-orange-500 px-3 py-2 text-sm font-semibold text-white hover:bg-orange-600"
              >
                Talk to sales
              </a>
            </div>
          )}
        </div>
      </div>

      {upgradeTarget && <UpgradeDialog plan={upgradeTarget} onClose={() => setUpgradeTarget(null)} />}
    </div>
  )
}

export default AccountBillingPage
