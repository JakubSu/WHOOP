import { type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../features/auth/store/authStore'
import { Spinner } from '../../shared/components/ui'

type ProtectedRouteProps = {
  children: ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation()
  const status = useAuthStore((state) => state.status)

  if (status === 'idle' || status === 'checking') {
    return (
      <main className="grid min-h-screen place-items-center bg-background p-6">
        <p className="flex items-center gap-2 text-sm text-muted-foreground"><Spinner className="size-4" />Loading your session...</p>
      </main>
    )
  }

  if (status !== 'authenticated') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return children
}
