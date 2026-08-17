import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './ProtectedRoute'
import { useAuthBootstrap } from '../../features/auth/hooks/useAuthBootstrap'
import { LoginPage } from '../../features/auth/pages/LoginPage'
import { RegisterPage } from '../../features/auth/pages/RegisterPage'
import { ConnectWhoopPage } from '../../features/whoop/pages/ConnectWhoopPage'
import { ConnectWhoopSuccessPage } from '../../features/whoop/pages/ConnectWhoopSuccessPage'
import { WeekPage } from '../../features/training/pages/WeekPage'
import { WorkoutPage } from '../../features/training/pages/WorkoutPage'
import { TrainingLandingPage } from '../../features/training/pages/TrainingLandingPage'

export function AppRouter() {
  useAuthBootstrap()

  return (
    <Routes>
      <Route path="/" element={<ProtectedRoute><TrainingLandingPage /></ProtectedRoute>} />
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
        path="/week"
        element={
          <ProtectedRoute>
            <WeekPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workouts/:workoutId"
        element={
          <ProtectedRoute>
            <WorkoutPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
