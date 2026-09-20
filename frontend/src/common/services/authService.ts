import { apiFormRequest, apiRequest } from './api'
import type { PlanId } from '../types/account'

export interface RegisterPayload {
  username: string
  password: string
  email: string
  plan: PlanId
}

// Matches fireguard-api/app/schemas.py::UserResponse.
export interface RegisterResult {
  id: string
  username: string
  plan: PlanId
  email_verified: boolean
  payment_required: boolean
  checkout_id: string | null
  amount: number | null
  currency: string
}

export interface TokenResult {
  access_token: string
  token_type: string
  expires_in: number
}

export function registerAccount(payload: RegisterPayload): Promise<RegisterResult> {
  return apiRequest<RegisterResult>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function login(username: string, password: string): Promise<TokenResult> {
  return apiFormRequest<TokenResult>('/auth/token', { username, password, grant_type: 'password' })
}
