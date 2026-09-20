import { apiRequest } from './api'
import type { AccountResponse } from '../types/account'

export function fetchAccount(token: string): Promise<AccountResponse> {
  return apiRequest<AccountResponse>('/account/me', { token })
}
