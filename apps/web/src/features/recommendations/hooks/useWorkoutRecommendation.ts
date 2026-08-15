import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { listExercises } from '../../training/api/trainingApi'
import { approveRecommendation, approveRecommendationOperation, getRecommendation, rejectRecommendation, rejectRecommendationOperation, saveRecommendationOperation } from '../api/recommendationApi'
import { type Recommendation, type RecommendationOperation } from '../types'
import { existingWorkoutIds } from '../services/workoutCard'

/** Loads and mutates a recommendation explicitly identified by the coach flow. */
export function useRecommendation(
  recommendationId: string | null | undefined,
  workoutId?: string,
  enabled = true,
) {
  const client = useQueryClient()
  const key = ['recommendation', recommendationId] as const
  const recommendation = useQuery<Recommendation>({
    queryKey: key,
    queryFn: () => getRecommendation(recommendationId!),
    enabled: enabled && Boolean(recommendationId),
  })
  const library = useQuery({
    queryKey: ['exercises'],
    queryFn: () => listExercises(),
    enabled: enabled && Boolean(recommendationId),
  })
  const storeRecommendation = (nextRecommendation: Recommendation) => {
    client.setQueryData(key, nextRecommendation)
    const affectedWorkoutIds = existingWorkoutIds(nextRecommendation.groups)
    return Promise.all([
      ...affectedWorkoutIds.flatMap((id) => [
        client.invalidateQueries({ queryKey: ['workout', id] }),
        client.invalidateQueries({ queryKey: ['workout-exercises', id] }),
      ]),
      ...(workoutId ? [
        client.invalidateQueries({ queryKey: ['workout', workoutId] }),
        client.invalidateQueries({ queryKey: ['workout-exercises', workoutId] }),
      ] : []),
      client.invalidateQueries({ queryKey: ['workouts'] }),
    ])
  }
  const save = useMutation({
    mutationFn: (operation: RecommendationOperation) => saveRecommendationOperation(recommendation.data?.id ?? '', operation),
    onSuccess: storeRecommendation,
  })
  const accept = useMutation({
    mutationFn: (operationId: string) => approveRecommendationOperation(recommendation.data?.id ?? '', operationId),
    onSuccess: storeRecommendation,
  })
  const reject = useMutation({
    mutationFn: (operationId: string) => rejectRecommendationOperation(recommendation.data?.id ?? '', operationId),
    onSuccess: storeRecommendation,
  })
  const acceptAll = useMutation({
    mutationFn: () => approveRecommendation(recommendation.data?.id ?? ''),
    onSuccess: storeRecommendation,
  })
  const rejectAll = useMutation({
    mutationFn: () => rejectRecommendation(recommendation.data?.id ?? ''),
    onSuccess: storeRecommendation,
  })
  return {
    recommendation: recommendation.data ?? null,
    exerciseLibrary: library.data ?? [],
    saveOperation: (operation: RecommendationOperation) => save.mutate(operation),
    acceptOperation: (id: string) => accept.mutateAsync(id),
    rejectOperation: (id: string) => reject.mutateAsync(id),
    acceptAll: () => acceptAll.mutateAsync(),
    rejectAll: () => rejectAll.mutateAsync(),
    savingOperationId: save.isPending ? save.variables.id : null,
    acceptingOperationId: accept.isPending ? accept.variables : null,
    rejectingOperationId: reject.isPending ? reject.variables : null,
    isBulkAccepting: acceptAll.isPending,
    isBulkRejecting: rejectAll.isPending,
    isLoading: recommendation.isLoading,
    error: recommendation.error ?? library.error ?? save.error ?? accept.error ?? reject.error ?? acceptAll.error ?? rejectAll.error,
  }
}
