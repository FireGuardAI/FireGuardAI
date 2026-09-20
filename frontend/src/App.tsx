import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './common/hooks/AuthProvider'
import { useAuth } from './common/hooks/useAuth'
import { RequireAuth } from './common/components/RequireAuth'
import { AppLayout } from './common/layouts/AppLayout'
import LoginPage from './modules/auth/pages/LoginPage'
import RegisterPage from './modules/auth/pages/RegisterPage'
import DashboardPage from './modules/dashboard/pages/DashboardPage'
import NewAnalysisPage from './modules/analysis/pages/NewAnalysisPage'
import AnalysisReportPage from './modules/analysis/pages/AnalysisReportPage'
import PricingPage from './modules/billing/pages/PricingPage'
import AccountBillingPage from './modules/billing/pages/AccountBillingPage'

function RootRedirect() {
  const { isAuthenticated, isLoading, token } = useAuth()
  if (token && isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">
        Loading your account…
      </div>
    )
  }
  return <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/pricing" element={<PricingPage />} />

          <Route
            path="/dashboard"
            element={
              <RequireAuth>
                <AppLayout>
                  <DashboardPage />
                </AppLayout>
              </RequireAuth>
            }
          />
          <Route
            path="/analysis/new"
            element={
              <RequireAuth>
                <AppLayout>
                  <NewAnalysisPage />
                </AppLayout>
              </RequireAuth>
            }
          />
          <Route
            path="/analysis/:id"
            element={
              <RequireAuth>
                <AppLayout>
                  <AnalysisReportPage />
                </AppLayout>
              </RequireAuth>
            }
          />
          <Route
            path="/account/billing"
            element={
              <RequireAuth>
                <AppLayout>
                  <AccountBillingPage />
                </AppLayout>
              </RequireAuth>
            }
          />

          <Route path="/" element={<RootRedirect />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
