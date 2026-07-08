import { useQuery } from '@tanstack/react-query'
import {
  listTrainingPlans,
  listTrainingPlanWorkouts,
} from '../api/trainingApi'

export function useTrainingPlanPage() {
  const plans = useQuery({
    queryKey: ['training-plans'],
    queryFn: listTrainingPlans,
  })
  const selectedPlan = plans.data?.[0] ?? null
  const workouts = useQuery({
    queryKey: ['training-plan-workouts', selectedPlan?.id],
    queryFn: () => listTrainingPlanWorkouts(selectedPlan?.id ?? ''),
    enabled: Boolean(selectedPlan?.id),
  })

  return {
    selectedPlan,
    workoutItems: workouts.data ?? [],
    isLoading: plans.isLoading || workouts.isLoading,
    error: plans.error ?? workouts.error,
  }
}
