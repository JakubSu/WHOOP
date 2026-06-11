import { apiRequest } from '../../../shared/api/apiClient'
import { type Recommendation } from '../types'

export function generateRecommendation(workoutId: string) {
  return apiRequest<Recommendation>(
    `/recommendations/workouts/${workoutId}/generate/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
}

export function approveRecommendationOperation(
  recommendationId: string,
  operationId: string,
) {
  return apiRequest<Recommendation>(
    `/recommendations/${recommendationId}/operations/${operationId}/approve/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
}

export function rejectRecommendationOperation(
  recommendationId: string,
  operationId: string,
) {
  return apiRequest<Recommendation>(
    `/recommendations/${recommendationId}/operations/${operationId}/reject/`,
    {
      method: 'POST',
      body: JSON.stringify({}),
    },
  )
}
