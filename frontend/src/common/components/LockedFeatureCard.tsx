import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'
import { CheckIcon, LockIcon } from './icons'

export function LockedFeatureRow({
  title,
  availableOn,
  unlocked,
}: {
  title: string
  availableOn: string
  unlocked: boolean
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-3">
      <div className="flex items-center gap-3">
        <span
          className={`flex h-8 w-8 items-center justify-center rounded-full ${
            unlocked ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-400'
          }`}
        >
          {unlocked ? <CheckIcon className="h-4 w-4" /> : <LockIcon className="h-4 w-4" />}
        </span>
        <div>
          <p className="text-sm font-medium text-slate-900">{title}</p>
          <p className="text-xs text-slate-500">{unlocked ? 'Included on your plan' : `Available on ${availableOn}`}</p>
        </div>
      </div>
      {!unlocked && (
        <Link
          to="/pricing"
          className="rounded-md border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:border-slate-300 hover:bg-slate-50"
        >
          Unlock
        </Link>
      )}
    </div>
  )
}

export function LockedFeatureCard({
  icon,
  title,
  description,
  availableOn,
}: {
  icon: ReactNode
  title: string
  description: string
  availableOn: string
}) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-white p-5">
      <div className="pointer-events-none absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-400">
        <LockIcon className="h-4 w-4" />
      </div>
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-orange-50 text-orange-600">
        {icon}
      </div>
      <p className="text-sm font-semibold text-slate-900">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{description}</p>
      <p className="mt-3 text-xs font-medium uppercase tracking-wide text-slate-400">Included in {availableOn}</p>
      <Link
        to="/pricing"
        className="mt-4 inline-flex rounded-md bg-orange-500 px-3 py-1.5 text-xs font-semibold text-white hover:bg-orange-600"
      >
        Upgrade to unlock
      </Link>
    </div>
  )
}
