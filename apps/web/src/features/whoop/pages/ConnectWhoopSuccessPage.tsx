import { useQueryClient } from '@tanstack/react-query'
import { CheckCircle2 } from 'lucide-react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCurrentUser } from '../../auth/api/authApi'
import { useAuthStore } from '../../auth/store/authStore'
import { AuthShell } from '../../../shared/components/AuthShell'

export function ConnectWhoopSuccessPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const setUser = useAuthStore((state) => state.setUser)

  useEffect(() => {
    let isMounted = true

    async function completeConnection() {
      try {
        const user = await getCurrentUser()
        if (isMounted) {
          setUser(user)
          await queryClient.invalidateQueries()
        }
      } finally {
        if (isMounted) {
          navigate('/', { replace: true })
        }
      }
    }

    void completeConnection()

    return () => {
      isMounted = false
    }
  }, [navigate, queryClient, setUser])

  return (
    <AuthShell
      eyebrow="Connected"
      title="Finalizing WHOOP"
      description="We are refreshing your profile and preparing your training workspace."
      icon={<CheckCircle2 aria-hidden="true" />}
    >
      <div className="status-card">
        <span className="spinner" aria-hidden="true" />
        <p>Finishing connection...</p>
      </div>
    </AuthShell>
  )
}
