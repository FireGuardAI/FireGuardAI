import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading, token } = useAuth()
  const location = useLocation()

  if (token && isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">
        Loading your account…
      </div>
    )
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  return <>{children}</>
}
