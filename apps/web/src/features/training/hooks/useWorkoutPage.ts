import { useQuery } from '@tanstack/react-query'
import {
  getWorkout,
  getWorkoutLanding,
  listWorkoutExercises,
} from '../api/trainingApi'
import { buildExerciseDisplays, getLocalDateIso, isDateToday } from '../services/formatters'

export function useWorkoutPage(workoutId: string | undefined) {
  const today = getLocalDateIso()
  const landing = useQuery({
    queryKey: ['workout-landing', today],
    queryFn: () => getWorkoutLanding(today),
    enabled: !workoutId,
  })
  const selectedWorkout = landing.data?.selected_workout ?? null
  const resolvedWorkoutId = workoutId ?? selectedWorkout?.id
  const workout = useQuery({
    queryKey: ['workout', resolvedWorkoutId],
    queryFn: () => getWorkout(resolvedWorkoutId ?? ''),
    enabled: Boolean(resolvedWorkoutId),
  })
  const workoutExercises = useQuery({
    queryKey: ['workout-exercises', resolvedWorkoutId],
    queryFn: () => listWorkoutExercises(resolvedWorkoutId ?? ''),
    enabled: Boolean(resolvedWorkoutId),
  })

  const exerciseDisplays = buildExerciseDisplays(
    workoutExercises.data ?? [],
  )
  const currentWorkout = workout.data ?? selectedWorkout
  const isToday = selectedWorkout?.is_today ?? isDateToday(currentWorkout?.date ?? null, today)

  return {
    resolvedWorkoutId,
    workout: currentWorkout,
    exerciseDisplays,
    isToday,
    landingMessage: landing.data?.message ?? null,
    isLoading:
      landing.isLoading || workout.isLoading || workoutExercises.isLoading,
    error: landing.error ?? workout.error ?? workoutExercises.error,
  }
}
