import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { PLAN_CATALOG } from '../types/account'
import { initialsOf } from '../utils/format'
import { CreditCardIcon, FlameIcon, GridIcon, LogOutIcon, PlusIcon, SparklesIcon } from './icons'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: GridIcon },
  { to: '/analysis/new', label: 'New analysis', icon: PlusIcon },
]

const ACCOUNT_ITEMS = [
  { to: '/pricing', label: 'Plans & pricing', icon: SparklesIcon },
  { to: '/account/billing', label: 'Account & billing', icon: CreditCardIcon },
]

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { account, signOut } = useAuth()

  function handleSignOut() {
    signOut()
    navigate('/login')
  }

  return (
    <div className="flex h-full w-64 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center gap-2 px-5 py-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500 text-white">
          <FlameIcon className="h-4.5 w-4.5" />
        </span>
        <span className="text-base font-semibold text-slate-900">
          FireGuard<span className="text-orange-500">AI</span>
        </span>
      </div>

      <nav className="flex-1 space-y-6 px-3">
        <ul className="space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to
            return (
              <li key={to}>
                <Link
                  to={to}
                  onClick={onNavigate}
                  className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    active ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Icon className="h-4.5 w-4.5" />
                  {label}
                </Link>
              </li>
            )
          })}
        </ul>

        <div>
          <p className="px-3 text-xs font-semibold uppercase tracking-wide text-slate-400">Account</p>
          <ul className="mt-2 space-y-1">
            {ACCOUNT_ITEMS.map(({ to, label, icon: Icon }) => {
              const active = location.pathname === to
              return (
                <li key={to}>
                  <Link
                    to={to}
                    onClick={onNavigate}
                    className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      active ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <Icon className="h-4.5 w-4.5" />
                    {label}
                  </Link>
                </li>
              )
            })}
          </ul>
        </div>
      </nav>

      {account && (
        <div className="border-t border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
              {initialsOf(account.username)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-900">{account.username}</p>
              <p className="truncate text-xs text-slate-500">{account.email ?? 'No email on file'}</p>
            </div>
            <button
              type="button"
              onClick={handleSignOut}
              aria-label="Sign out"
              className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            >
              <LogOutIcon className="h-4 w-4" />
            </button>
          </div>
          <div className="mt-3 flex items-center justify-between">
            <span className="inline-flex items-center rounded-full border border-sky-200 bg-sky-50 px-2.5 py-0.5 text-xs font-medium text-sky-700">
              {PLAN_CATALOG[account.plan].name} plan
            </span>
            {account.plan !== 'government' && (
              <Link to="/pricing" onClick={onNavigate} className="text-xs font-medium text-orange-600 hover:text-orange-700">
                Upgrade
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
