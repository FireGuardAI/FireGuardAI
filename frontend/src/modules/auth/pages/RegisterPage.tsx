import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { PLAN_CATALOG, PLAN_ORDER } from '../../../common/types/account'
import type { PlanId } from '../../../common/types/account'
import { useAuth } from '../../../common/hooks/useAuth'
import { confirmMockPayment } from '../../../common/services/billingService'
import { ApiError } from '../../../common/services/api'
import { StepIndicator } from '../../../common/components/StepIndicator'
import { FlameIcon, GraduationCapIcon } from '../../../common/components/icons'
import { formatLkr } from '../../../common/utils/format'

const USERNAME_PATTERN = /^[a-zA-Z0-9_.-]{3,120}$/
const SALES_EMAIL = 'sales@fireguardai.app'

function isValidPlan(value: string | null): value is PlanId {
  return value !== null && (PLAN_ORDER as string[]).includes(value)
}

function RegisterPage() {
  const [searchParams] = useSearchParams()
  const initialPlan = isValidPlan(searchParams.get('plan')) ? (searchParams.get('plan') as PlanId) : 'student'

  const { signUp, signIn } = useAuth()
  const navigate = useNavigate()

  const [step, setStep] = useState(0)
  const [selectedPlan, setSelectedPlan] = useState<PlanId>(initialPlan)

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [checkoutId, setCheckoutId] = useState<string | null>(null)

  const plan = PLAN_CATALOG[selectedPlan]
  const isFreePlan = plan.billingModel === 'free'
  const isContactSales = plan.billingModel === 'contact-sales'
  const steps = isFreePlan ? ['Choose plan', 'Your details'] : ['Choose plan', 'Your details', 'Payment']

  async function handleDetailsSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)

    if (!USERNAME_PATTERN.test(username)) {
      setFormError('Username must be 3-120 characters: letters, numbers, dots, hyphens or underscores only.')
      return
    }
    if (password.length < 12) {
      setFormError('Password must be at least 12 characters.')
      return
    }
    if (plan.requiresInstitutionalEmail === false && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      setFormError('Enter a valid email address.')
      return
    }

    setIsSubmitting(true)
    try {
      const result = await signUp({ username, password, email, plan: selectedPlan })
      if (isFreePlan) {
        await signIn(username, password)
        navigate('/dashboard', { replace: true })
        return
      }
      setCheckoutId(result.checkout_id)
      setStep(2)
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Registration failed. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleConfirmPayment() {
    if (!checkoutId) return
    setFormError(null)
    setIsSubmitting(true)
    try {
      const token = await signIn(username, password)
      await confirmMockPayment(token, checkoutId)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Could not confirm the mock payment. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleFinishLater() {
    setFormError(null)
    setIsSubmitting(true)
    try {
      await signIn(username, password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Could not sign you in. Please try again from the login page.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-white px-6 py-10">
      <div className="mx-auto max-w-3xl">
        <Link to="/login" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500 text-white">
            <FlameIcon className="h-4.5 w-4.5" />
          </span>
          <span className="text-base font-semibold text-slate-900">
            FireGuard<span className="text-orange-500">AI</span>
          </span>
        </Link>

        <div className="mt-8">
          <StepIndicator steps={steps} currentIndex={step} />
        </div>

        {step === 0 && (
          <section className="mt-8">
            <h1 className="text-2xl font-semibold text-slate-900">Create your account</h1>
            <p className="mt-1 text-sm text-slate-500">Start with the plan that matches how you audit. You can change it any time.</p>

            <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {PLAN_ORDER.map((id) => {
                const item = PLAN_CATALOG[id]
                const selected = id === selectedPlan
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setSelectedPlan(id)}
                    className={`relative rounded-xl border p-5 text-left transition-colors ${
                      selected ? 'border-orange-500 shadow-sm ring-1 ring-orange-500' : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    {id === 'student' && (
                      <GraduationCapIcon className="absolute right-4 top-4 h-4.5 w-4.5 text-sky-500" />
                    )}
                    <p className="text-sm font-semibold text-slate-900">{item.name}</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900">
                      {item.mockAmount === null ? (item.billingModel === 'contact-sales' ? 'Custom' : 'Free') : formatLkr(item.mockAmount)}
                    </p>
                    <p className="text-xs text-slate-500">
                      {item.billingModel === 'per-report'
                        ? 'per report credit'
                        : item.billingModel === 'subscription'
                          ? 'per month'
                          : item.billingModel === 'contact-sales'
                            ? 'annual agreement'
                            : 'with verified institutional email'}
                    </p>
                    <p className="mt-3 text-sm text-slate-600">{item.tagline}</p>
                    <p className="mt-3 text-xs text-slate-400">
                      {item.analysisInput} · {item.reportLimitLabel}
                    </p>
                  </button>
                )
              })}
            </div>

            <div className="mt-6 flex flex-col items-center justify-between gap-4 sm:flex-row">
              <Link to="/pricing" className="text-sm font-medium text-orange-600 hover:text-orange-700">
                Compare plans in detail
              </Link>
              {isContactSales ? (
                <a
                  href={`mailto:${SALES_EMAIL}?subject=${encodeURIComponent('Government plan inquiry')}`}
                  className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
                >
                  Talk to sales
                </a>
              ) : (
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="rounded-lg bg-orange-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-orange-600"
                >
                  Continue with {plan.name}
                </button>
              )}
            </div>

            <p className="mt-8 text-center text-sm text-slate-500">
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-orange-600 hover:text-orange-700">
                Sign in
              </Link>
            </p>
          </section>
        )}

        {step === 1 && (
          <section className="mt-8 max-w-md">
            <h1 className="text-2xl font-semibold text-slate-900">Your details</h1>
            <p className="mt-1 text-sm text-slate-500">
              Registering on the <span className="font-medium text-slate-700">{plan.name}</span> plan.
            </p>

            <form className="mt-6 space-y-4" onSubmit={handleDetailsSubmit}>
              <div>
                <label htmlFor="username" className="mb-1 block text-sm font-medium text-slate-700">
                  Username
                </label>
                <input
                  id="username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  required
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
                  placeholder="dana_reyes"
                />
                <p className="mt-1 text-xs text-slate-400">Letters, numbers, dots, hyphens and underscores only.</p>
              </div>

              <div>
                <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">
                  {plan.requiresInstitutionalEmail ? 'Institutional email' : 'Email'}
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
                  placeholder={plan.requiresInstitutionalEmail ? 'you@sliit.lk' : 'you@company.com'}
                />
                {plan.requiresInstitutionalEmail && (
                  <p className="mt-1 text-xs text-slate-400">
                    Student accounts require a verified institutional domain (e.g. @sliit.lk, @uom.lk).
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  minLength={12}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
                  placeholder="At least 12 characters"
                />
              </div>

              {formError && <p className="text-sm text-red-600">{formError}</p>}

              <div className="flex items-center justify-between pt-2">
                <button type="button" onClick={() => setStep(0)} className="text-sm font-medium text-slate-500 hover:text-slate-700">
                  Back
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-lg bg-orange-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? 'Please wait…' : isFreePlan ? 'Create account' : 'Continue to payment'}
                </button>
              </div>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500">
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-orange-600 hover:text-orange-700">
                Sign in
              </Link>
            </p>
          </section>
        )}

        {step === 2 && (
          <section className="mt-8 max-w-md">
            <h1 className="text-2xl font-semibold text-slate-900">Payment</h1>
            <p className="mt-1 text-sm text-slate-500">
              This is a mock checkout — no real payment is taken in this environment.
            </p>

            <div className="mt-6 flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
              <span className="text-sm font-medium text-slate-700">{plan.name} plan</span>
              <span className="text-sm font-semibold text-slate-900">
                {plan.mockAmount !== null ? formatLkr(plan.mockAmount) : 'Custom'}
              </span>
            </div>

            {formError && <p className="mt-4 text-sm text-red-600">{formError}</p>}

            <button
              type="button"
              onClick={handleConfirmPayment}
              disabled={isSubmitting}
              className="mt-6 w-full rounded-lg bg-orange-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? 'Confirming…' : 'Confirm mock payment'}
            </button>
            <button
              type="button"
              onClick={handleFinishLater}
              disabled={isSubmitting}
              className="mt-3 w-full text-center text-sm font-medium text-slate-500 hover:text-slate-700"
            >
              I'll pay later — take me to the dashboard
            </button>
          </section>
        )}
      </div>
    </div>
  )
}

export default RegisterPage
