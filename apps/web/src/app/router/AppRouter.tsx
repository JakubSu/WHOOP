import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './ProtectedRoute'
import { useAuthBootstrap } from '../../features/auth/hooks/useAuthBootstrap'
import { LoginPage } from '../../features/auth/pages/LoginPage'
import { RegisterPage } from '../../features/auth/pages/RegisterPage'
import { ConnectWhoopPage } from '../../features/whoop/pages/ConnectWhoopPage'
import { ConnectWhoopSuccessPage } from '../../features/whoop/pages/ConnectWhoopSuccessPage'
import { PlanPlaceholderPage } from '../../features/plan/pages/PlanPlaceholderPage'

export function AppRouter() {
  useAuthBootstrap()

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/connect-whoop"
        element={
          <ProtectedRoute>
            <ConnectWhoopPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/connect-whoop/success"
        element={
          <ProtectedRoute>
            <ConnectWhoopSuccessPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/plan"
        element={
          <ProtectedRoute>
            <PlanPlaceholderPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
