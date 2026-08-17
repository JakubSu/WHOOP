import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Navigate, useNavigate } from 'react-router-dom'
import { getLocalDateIso } from '../services/formatters'
import { getWorkoutLanding } from '../api/trainingApi'

export function TrainingLandingPage() {
  const navigate = useNavigate()
  const today = getLocalDateIso()
  const landing = useQuery({ queryKey: ['workout-landing', today], queryFn: () => getWorkoutLanding(today) })

  useEffect(() => {
    if (!landing.data) return
    navigate(landing.data.selected_workout ? `/workouts/${landing.data.selected_workout.id}` : '/week', { replace: true })
  }, [landing.data, navigate])

  if (landing.isError) return <Navigate to="/week" replace />
  return <main className="status-screen"><p>Finding your next workout...</p></main>
}
