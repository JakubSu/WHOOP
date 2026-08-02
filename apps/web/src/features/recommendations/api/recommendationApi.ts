import { apiRequest } from '../../../shared/api/apiClient'
import {
  type Recommendation,
  type RecommendationOperationStatus,
} from '../types'

type ApiRecommendation = Omit<Recommendation, 'operations'> & {
  operation_type: Recommendation['operations'][number]['operation_type']
  payload: Record<string, unknown>
  display_text: string
}

export async function getPendingWorkoutRecommendation(workoutId: string) {
  const recommendations = await apiRequest<ApiRecommendation[]>(
    '/recommendations/?status=pending',
  )
  const recommendation = recommendations.find(
    (item) => item.workout_id === workoutId,
  )
  return recommendation ? normalizeRecommendation(recommendation) : null
}

export async function approveRecommendationOperation(
  recommendationId: string,
  _operationId: string,
) {
  const recommendation = await apiRequest<ApiRecommendation>(
    `/recommendations/${recommendationId}/accept/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
  return normalizeRecommendation(recommendation)
}

export async function rejectRecommendationOperation(
  recommendationId: string,
  _operationId: string,
) {
  const recommendation = await apiRequest<ApiRecommendation>(
    `/recommendations/${recommendationId}/reject/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
  return normalizeRecommendation(recommendation)
}

export function normalizeRecommendation(
  recommendation: ApiRecommendation | Recommendation,
): Recommendation {
  if ('operations' in recommendation) {
    return recommendation
  }

  const { operation_type, payload, display_text, ...rest } = recommendation
  return {
    ...rest,
    operations: [
      {
        id: recommendation.id,
        sequence: 1,
        operation_type,
        status: operationStatusFromRecommendationStatus(recommendation.status),
        payload,
        display_text,
      },
    ],
  }
}

function operationStatusFromRecommendationStatus(
  status: Recommendation['status'],
): RecommendationOperationStatus {
  if (status === 'applied') {
    return 'accepted'
  }
  if (status === 'rejected' || status === 'stale' || status === 'failed') {
    return status
  }
  return 'pending'
}
