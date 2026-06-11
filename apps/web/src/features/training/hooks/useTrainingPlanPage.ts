import { useQuery } from '@tanstack/react-query'
import {
  listTrainingPlans,
  listWorkoutExercises,
  listWorkouts,
} from '../api/trainingApi'
import { buildWorkoutListItems } from '../services/formatters'

export function useTrainingPlanPage() {
  const plans = useQuery({
    queryKey: ['training-plans'],
    queryFn: listTrainingPlans,
  })
  const workouts = useQuery({
    queryKey: ['workouts'],
    queryFn: listWorkouts,
  })
  const workoutExercises = useQuery({
    queryKey: ['workout-exercises'],
    queryFn: listWorkoutExercises,
  })

  const selectedPlan = plans.data?.[0] ?? null
  const planWorkouts = selectedPlan
    ? (workouts.data ?? []).filter((workout) => workout.plan === selectedPlan.id)
    : []
  const workoutItems = buildWorkoutListItems(
    planWorkouts,
    workoutExercises.data ?? [],
  )

  return {
    selectedPlan,
    workoutItems,
    isLoading: plans.isLoading || workouts.isLoading || workoutExercises.isLoading,
    error: plans.error ?? workouts.error ?? workoutExercises.error,
  }
}
