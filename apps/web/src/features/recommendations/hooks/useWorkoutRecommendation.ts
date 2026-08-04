import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { listExercises } from '../../training/api/trainingApi'
import { approveRecommendationOperation, getRecommendation, rejectRecommendationOperation, saveRecommendationOperation } from '../api/recommendationApi'
import { type Recommendation, type RecommendationOperation } from '../types'

const TEST_RECOMMENDATION_ID = '10000000-0000-4000-8000-000000000003'
const TEST_WORKOUT_ID = 'b85f256c-b973-4f47-9831-668625a81287'

export function useWorkoutRecommendation(workoutId: string | undefined) {
  const client = useQueryClient()
  const key = ['recommendation', workoutId] as const
  const recommendation = useQuery<Recommendation>({
    queryKey: key,
    queryFn: () => getRecommendation(TEST_RECOMMENDATION_ID),
    enabled: workoutId === TEST_WORKOUT_ID,
  })
  const library = useQuery({ queryKey: ['exercises'], queryFn: listExercises })
  const refresh = () => Promise.all([
    client.invalidateQueries({ queryKey: key }),
    client.invalidateQueries({ queryKey: ['workout', workoutId] }),
    client.invalidateQueries({ queryKey: ['workout-exercises', workoutId] }),
    client.invalidateQueries({ queryKey: ['workouts'] }),
  ])
  const save = useMutation({
    mutationFn: (operation: RecommendationOperation) => saveRecommendationOperation(recommendation.data?.id ?? '', operation),
    onSuccess: refresh,
  })
  const accept = useMutation({
    mutationFn: (operationId: string) => approveRecommendationOperation(recommendation.data?.id ?? '', operationId),
    onSuccess: refresh,
  })
  const reject = useMutation({
    mutationFn: (operationId: string) => rejectRecommendationOperation(recommendation.data?.id ?? '', operationId),
    onSuccess: refresh,
  })
  return { recommendation: recommendation.data ?? null, exerciseLibrary: library.data ?? [], saveOperation: (operation: RecommendationOperation) => save.mutate(operation), acceptOperation: (id: string) => accept.mutate(id), rejectOperation: (id: string) => reject.mutate(id), savingOperationId: save.isPending ? save.variables.id : null, acceptingOperationId: accept.isPending ? accept.variables : null, rejectingOperationId: reject.isPending ? reject.variables : null, isLoading: recommendation.isLoading, error: recommendation.error ?? library.error ?? save.error ?? accept.error ?? reject.error }
}
