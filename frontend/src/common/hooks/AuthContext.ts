import { createContext } from 'react'
import type { AccountResponse } from '../types/account'
import type { RegisterPayload, RegisterResult } from '../services/authService'

export interface AuthContextValue {
  token: string | null
  account: AccountResponse | null
  isLoading: boolean
  isAuthenticated: boolean
  signIn: (username: string, password: string) => Promise<string>
  signUp: (payload: RegisterPayload) => Promise<RegisterResult>
  signOut: () => void
  refreshAccount: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
