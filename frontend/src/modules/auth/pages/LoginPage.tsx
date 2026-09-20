import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../../common/hooks/useAuth'
import { ApiError } from '../../../common/services/api'
import { FlameIcon, ShieldCheckIcon } from '../../../common/components/icons'

const HIGHLIGHTS = [
  { label: 'Automated', detail: 'Retrieval + compliance audit in one pipeline' },
  { label: 'Explainable', detail: 'Every finding cites its source clause' },
  { label: 'Multi-tier', detail: 'Plans for students through government agencies' },
]

function LoginPage() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await signIn(username, password)
      const from = (location.state as { from?: { pathname: string; search: string } } | null)?.from
      navigate(from ? `${from.pathname}${from.search}` : '/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to sign in. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <div className="flex flex-col justify-between bg-slate-950 px-8 py-10 text-white lg:w-1/2 lg:px-16 lg:py-16">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500">
              <FlameIcon className="h-4.5 w-4.5" />
            </span>
            <span className="text-base font-semibold">FireGuardAI</span>
          </div>

          <h1 className="mt-16 max-w-lg text-3xl font-semibold leading-tight sm:text-4xl">
            Fire code compliance, audited in minutes instead of weeks.
          </h1>
          <p className="mt-4 max-w-md text-sm text-slate-300">
            Describe a building or upload its plans. FireGuardAI retrieves the applicable code sections, audits
            every clause and returns a cited pass/fail report your AHJ can read.
          </p>

          <div className="mt-10 flex flex-wrap gap-x-10 gap-y-4 border-t border-white/10 pt-6">
            {HIGHLIGHTS.map((item) => (
              <div key={item.label}>
                <p className="text-sm font-semibold text-white">{item.label}</p>
                <p className="text-xs text-slate-400">{item.detail}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-start gap-2 text-xs text-slate-400">
          <ShieldCheckIcon className="mt-0.5 h-4 w-4 shrink-0" />
          <span>Reports are advisory and do not replace an AHJ inspection.</span>
        </div>
      </div>

      <div className="flex flex-1 items-center justify-center bg-white px-6 py-16">
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Sign in</h2>
          <p className="mt-1 text-sm text-slate-500">Welcome back. Pick up where your last audit left off.</p>

          <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="username" className="mb-1 block text-sm font-medium text-slate-700">
                Username
              </label>
              <input
                id="username"
                type="text"
                required
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
                placeholder="e.g. dana_reyes"
              />
            </div>

            <div>
              <div className="mb-1 flex items-center justify-between">
                <label htmlFor="password" className="block text-sm font-medium text-slate-700">
                  Password
                </label>
                <span
                  title="Password reset isn't available yet — contact support."
                  className="cursor-default text-xs font-medium text-slate-400"
                >
                  Forgot?
                </span>
              </div>
              <input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
                placeholder="••••••••••••"
              />
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-lg bg-orange-500 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            No account yet?{' '}
            <Link to="/register" className="font-medium text-orange-600 hover:text-orange-700">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
