import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import LoginPage from './modules/auth/pages/LoginPage'
import DashboardPage from './modules/dashboard/pages/DashboardPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />

        <Route path="/" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App