import { useQuery } from '@tanstack/react-query'
import {
  getWorkout,
  listExercises,
  listWorkoutExercises,
} from '../api/trainingApi'
import { buildExerciseDisplays } from '../services/formatters'

export function useWorkoutPage(workoutId: string | undefined) {
  const workout = useQuery({
    queryKey: ['workout', workoutId],
    queryFn: () => getWorkout(workoutId ?? ''),
    enabled: Boolean(workoutId),
  })
  const workoutExercises = useQuery({
    queryKey: ['workout-exercises'],
    queryFn: listWorkoutExercises,
  })
  const exercises = useQuery({
    queryKey: ['exercises'],
    queryFn: listExercises,
  })

  const filteredWorkoutExercises = (workoutExercises.data ?? []).filter(
    (item) => item.workout === workoutId,
  )
  const exerciseDisplays = buildExerciseDisplays(
    filteredWorkoutExercises,
    exercises.data ?? [],
  )

  return {
    workout: workout.data ?? null,
    exerciseDisplays,
    isLoading: workout.isLoading || workoutExercises.isLoading || exercises.isLoading,
    error: workout.error ?? workoutExercises.error ?? exercises.error,
  }
}
