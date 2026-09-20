import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../../common/hooks/useAuth'
import { listAnalysisRecords } from '../../../common/services/analysisService'
import { StatusBadge } from '../../../common/components/StatusBadge'
import { UsagePanel } from '../../../common/components/UsagePanel'
import { LockedFeatureCard } from '../../../common/components/LockedFeatureCard'
import { PLAN_CATALOG } from '../../../common/types/account'
import { formatDate } from '../../../common/utils/format'
import { CheckCircleIcon, FileTextIcon, PlusIcon, SearchIcon, SparklesIcon, UploadCloudIcon } from '../../../common/components/icons'

function DashboardPage() {
  const { account } = useAuth()
  const [query, setQuery] = useState('')

  const history = useMemo(() => (account ? listAnalysisRecords(account.id) : []), [account])
  const filtered = useMemo(
    () => history.filter((record) => record.buildingName.toLowerCase().includes(query.toLowerCase())),
    [history, query],
  )

  const stats = useMemo(() => {
    const failing = history.filter((record) => record.overallStatus.toUpperCase() === 'NON_COMPLIANT').length
    const openItems = history.filter((record) =>
      record.detailedChecks.some((check) => check.status === 'PARTIAL' || check.status === 'INSUFFICIENT_DATA'),
    ).length
    return { total: history.length, openItems, failing }
  }, [history])

  if (!account) return null
  const plan = PLAN_CATALOG[account.plan]

  return (
    <div>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{plan.name} account</p>
          <h1 className="mt-1 text-2xl font-semibold text-slate-900">Compliance overview</h1>
          <p className="mt-1 text-sm text-slate-500">Every audit run on this account, with its current code status.</p>
        </div>
        <Link
          to="/analysis/new"
          className="inline-flex items-center gap-1.5 self-start rounded-lg bg-orange-500 px-4 py-2 text-sm font-semibold text-white hover:bg-orange-600"
        >
          <PlusIcon className="h-4 w-4" />
          New analysis
        </Link>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">Recent analyses</h2>
            <div className="relative">
              <SearchIcon className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search buildings"
                className="rounded-lg border border-slate-200 py-1.5 pl-8 pr-3 text-sm focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
              />
            </div>
          </div>

          <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 bg-white">
            {filtered.length === 0 ? (
              <div className="flex flex-col items-center gap-2 px-6 py-14 text-center">
                <FileTextIcon className="h-8 w-8 text-slate-300" />
                <p className="text-sm font-medium text-slate-700">
                  {history.length === 0 ? 'No analyses yet' : 'No buildings match your search'}
                </p>
                {history.length === 0 && (
                  <>
                    <p className="text-sm text-slate-500">Run your first audit to see it show up here.</p>
                    <Link to="/analysis/new" className="mt-2 text-sm font-medium text-orange-600 hover:text-orange-700">
                      Start a new analysis
                    </Link>
                  </>
                )}
              </div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {filtered.map((record) => {
                  const ModeIcon = record.mode === 'pdf' ? UploadCloudIcon : FileTextIcon
                  return (
                    <li key={record.id}>
                      <Link
                        to={`/analysis/${record.id}`}
                        className="flex items-center gap-4 px-4 py-4 hover:bg-slate-50 sm:px-6"
                      >
                        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
                          <ModeIcon className="h-4.5 w-4.5" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-slate-900">{record.buildingName}</p>
                          <p className="text-xs text-slate-500">{record.mode === 'pdf' ? 'Building plan (PDF)' : 'Text description'}</p>
                        </div>
                        {record.complianceScore !== null && (
                          <div className="hidden text-right sm:block">
                            <p className="text-lg font-semibold text-slate-900">{Math.round(record.complianceScore)}</p>
                            <p className="text-xs text-slate-400">score</p>
                          </div>
                        )}
                        <p className="hidden text-sm text-slate-500 sm:block">{formatDate(record.submittedAt)}</p>
                        <StatusBadge status={record.overallStatus} />
                      </Link>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <UsagePanel account={account} />

          <div className="grid grid-cols-3 divide-x divide-slate-100 rounded-xl border border-slate-200 bg-white p-5 text-center">
            <div>
              <p className="text-xl font-semibold text-slate-900">{stats.total}</p>
              <p className="text-xs text-slate-500">Reports</p>
            </div>
            <div>
              <p className="text-xl font-semibold text-slate-900">{stats.openItems}</p>
              <p className="text-xs text-slate-500">Open items</p>
            </div>
            <div>
              <p className="text-xl font-semibold text-slate-900">{stats.failing}</p>
              <p className="text-xs text-slate-500">Failing</p>
            </div>
          </div>

          {!plan.features.pdfAnalysis ? (
            <LockedFeatureCard
              icon={<FileTextIcon className="h-4.5 w-4.5" />}
              title="Unlock PDF plan analysis"
              description="Upload architectural drawings and floor plans directly instead of describing them."
              availableOn="Basic, Pro, Enterprise and Government"
            />
          ) : !plan.features.externalApi ? (
            <LockedFeatureCard
              icon={<SparklesIcon className="h-4.5 w-4.5" />}
              title="Need programmatic access?"
              description="Enterprise and Government plans expose compliance audits through an external API."
              availableOn="Enterprise and Government"
            />
          ) : (
            <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-5">
              <CheckCircleIcon className="h-5 w-5 shrink-0 text-emerald-600" />
              <p className="text-sm text-emerald-800">You have full platform access on the {plan.name} plan.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
