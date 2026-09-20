import { apiRequest } from './api'
import type { PlanId } from '../types/account'

export interface CheckoutResult {
  checkout_id: string
  plan: PlanId
  amount: number
  currency: string
  status: string
}

export interface ConfirmResult {
  checkout_id: string
  plan: PlanId
  status: string
  message: string
}

export function startMockCheckout(token: string, plan: PlanId): Promise<CheckoutResult> {
  return apiRequest<CheckoutResult>('/billing/mock/checkout', {
    method: 'POST',
    token,
    body: JSON.stringify({ plan }),
  })
}

export function confirmMockPayment(token: string, checkoutId: string): Promise<ConfirmResult> {
  return apiRequest<ConfirmResult>('/billing/mock/confirm', {
    method: 'POST',
    token,
    body: JSON.stringify({ checkout_id: checkoutId }),
  })
}
