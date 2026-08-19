import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Navigate, useNavigate } from 'react-router-dom'
import { getLocalDateIso } from '../services/formatters'
import { getWorkoutLanding } from '../api/trainingApi'
import { Spinner } from '../../../shared/components/ui'
import { useAuthStore } from '../../auth/store/authStore'

export function TrainingLandingPage() {
  const navigate = useNavigate()
  const userId = useAuthStore((state) => state.user?.id)
  const today = getLocalDateIso()
  const landing = useQuery({
    queryKey: ['workout-landing', userId, today],
    queryFn: () => getWorkoutLanding(today),
    enabled: Boolean(userId),
  })

  useEffect(() => {
    if (!landing.data) return
    navigate(landing.data.selected_workout ? `/workouts/${landing.data.selected_workout.id}` : '/week', { replace: true })
  }, [landing.data, navigate])

  if (landing.isError) return <Navigate to="/week" replace />
  return <main className="grid min-h-screen place-items-center bg-background p-6"><p className="flex items-center gap-2 text-sm text-muted-foreground"><Spinner className="size-4" />Finding your next workout...</p></main>
}
