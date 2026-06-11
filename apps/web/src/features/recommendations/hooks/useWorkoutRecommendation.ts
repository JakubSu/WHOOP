import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  approveRecommendationOperation,
  generateRecommendation,
  rejectRecommendationOperation,
} from '../api/recommendationApi'
import { type Recommendation } from '../types'

export function useWorkoutRecommendation(workoutId: string | undefined) {
  const queryClient = useQueryClient()
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const generate = useMutation({
    mutationFn: () => generateRecommendation(workoutId ?? ''),
    onSuccess: setRecommendation,
  })
  const accept = useMutation({
    mutationFn: (operationId: string) =>
      approveRecommendationOperation(recommendation?.id ?? '', operationId),
    onSuccess: async (nextRecommendation) => {
      setRecommendation(nextRecommendation)
      await queryClient.invalidateQueries({ queryKey: ['workout', workoutId] })
      await queryClient.invalidateQueries({ queryKey: ['workout-exercises'] })
    },
  })
  const reject = useMutation({
    mutationFn: (operationId: string) =>
      rejectRecommendationOperation(recommendation?.id ?? '', operationId),
    onSuccess: (nextRecommendation) => {
      setRecommendation(nextRecommendation)
    },
  })

  return {
    recommendation,
    generate: () => {
      if (workoutId) {
        generate.mutate()
      }
    },
    acceptOperation: (operationId: string) => {
      if (recommendation) {
        accept.mutate(operationId)
      }
    },
    rejectOperation: (operationId: string) => {
      if (recommendation) {
        reject.mutate(operationId)
      }
    },
    isGenerating: generate.isPending,
    acceptingOperationId: accept.isPending ? accept.variables : null,
    rejectingOperationId: reject.isPending ? reject.variables : null,
    error: generate.error ?? accept.error ?? reject.error,
  }
}
