import { type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../features/auth/store/authStore'

type ProtectedRouteProps = {
  children: ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation()
  const status = useAuthStore((state) => state.status)

  if (status === 'idle' || status === 'checking') {
    return (
      <main className="status-screen">
        <p>Loading your session...</p>
      </main>
    )
  }

  if (status !== 'authenticated') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return children
}
