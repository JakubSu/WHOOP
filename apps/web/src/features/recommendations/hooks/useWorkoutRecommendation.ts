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
  const isWorkoutReadyToSave =
    recommendation?.status === 'accepted' &&
    recommendation.operations.every((operation) => operation.status === 'accepted')
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
  const saveWorkout = useMutation({
    mutationFn: async () => {
      await queryClient.invalidateQueries({ queryKey: ['workout', workoutId] })
      await queryClient.invalidateQueries({ queryKey: ['workout-exercises'] })
    },
    onSuccess: () => {
      setRecommendation(null)
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
    saveWorkout: () => {
      if (isWorkoutReadyToSave) {
        saveWorkout.mutate()
      }
    },
    isGenerating: generate.isPending,
    isSavingWorkout: saveWorkout.isPending,
    isWorkoutReadyToSave,
    acceptingOperationId: accept.isPending ? accept.variables : null,
    rejectingOperationId: reject.isPending ? reject.variables : null,
    error: generate.error ?? accept.error ?? reject.error ?? saveWorkout.error,
  }
}
