import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import type { AccountResponse } from '../types/account'
import { fetchAccount } from '../services/accountService'
import { login as loginRequest, registerAccount } from '../services/authService'
import type { RegisterPayload } from '../services/authService'
import { AuthContext } from './AuthContext'
import type { AuthContextValue } from './AuthContext'

const TOKEN_KEY = 'fireguard.token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [account, setAccount] = useState<AccountResponse | null>(null)
  // Lazily seeded from whether a token exists at mount, then only ever flipped
  // from event handlers (applyToken) or promise callbacks below — never
  // synchronously inside the effect body itself.
  const [fetchStatus, setFetchStatus] = useState<'idle' | 'pending'>(() =>
    localStorage.getItem(TOKEN_KEY) ? 'pending' : 'idle',
  )

  function applyToken(next: string | null) {
    setTokenState(next)
    if (next) {
      localStorage.setItem(TOKEN_KEY, next)
      setFetchStatus('pending')
    } else {
      localStorage.removeItem(TOKEN_KEY)
      setFetchStatus('idle')
      setAccount(null)
    }
  }

  useEffect(() => {
    if (!token) return
    let cancelled = false
    fetchAccount(token)
      .then((data) => {
        if (!cancelled) setAccount(data)
      })
      .catch(() => {
        if (!cancelled) applyToken(null)
      })
      .finally(() => {
        if (!cancelled) setFetchStatus('idle')
      })
    return () => {
      cancelled = true
    }
  }, [token])

  async function refreshAccount() {
    if (!token) {
      setAccount(null)
      return
    }
    const data = await fetchAccount(token)
    setAccount(data)
  }

  async function signIn(username: string, password: string) {
    const result = await loginRequest(username, password)
    applyToken(result.access_token)
    return result.access_token
  }

  function signUp(payload: RegisterPayload) {
    return registerAccount(payload)
  }

  function signOut() {
    applyToken(null)
  }

  const isLoading = fetchStatus === 'pending'

  const value: AuthContextValue = {
    token,
    account,
    isLoading,
    isAuthenticated: Boolean(token && account),
    signIn,
    signUp,
    signOut,
    refreshAccount,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
