import { useState } from 'react'
import { Modal } from './Modal'
import { PLAN_CATALOG } from '../types/account'
import type { PlanId } from '../types/account'
import { confirmMockPayment, startMockCheckout } from '../services/billingService'
import { ApiError } from '../services/api'
import { useAuth } from '../hooks/useAuth'
import { formatLkr } from '../utils/format'

export function UpgradeDialog({ plan, onClose }: { plan: PlanId; onClose: () => void }) {
  const { token, refreshAccount } = useAuth()
  const [status, setStatus] = useState<'idle' | 'working' | 'done' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)
  const definition = PLAN_CATALOG[plan]

  async function confirm() {
    if (!token) return
    setStatus('working')
    setError(null)
    try {
      const checkout = await startMockCheckout(token, plan)
      await confirmMockPayment(token, checkout.checkout_id)
      await refreshAccount()
      setStatus('done')
    } catch (err) {
      setStatus('error')
      setError(err instanceof ApiError ? err.message : 'Something went wrong while processing the mock payment.')
    }
  }

  return (
    <Modal title={`Upgrade to ${definition.name}`} onClose={onClose}>
      {status === 'done' ? (
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            Your account is now on the {definition.name} plan. New limits apply immediately.
          </p>
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Done
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            {definition.mockAmount !== null
              ? `This is a mock checkout — no real payment is taken. ${definition.billingModel === 'per-report' ? 'Confirming adds 5 report credits.' : 'Confirming activates an active subscription immediately.'}`
              : 'This plan is provisioned by our billing team.'}
          </p>
          <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
            <span className="text-sm font-medium text-slate-700">{definition.name} plan</span>
            <span className="text-sm font-semibold text-slate-900">
              {definition.mockAmount !== null ? formatLkr(definition.mockAmount) : 'Custom'}
            </span>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="button"
            disabled={status === 'working'}
            onClick={confirm}
            className="w-full rounded-md bg-orange-500 px-4 py-2 text-sm font-semibold text-white hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {status === 'working' ? 'Confirming…' : 'Confirm mock payment'}
          </button>
        </div>
      )}
    </Modal>
  )
}
