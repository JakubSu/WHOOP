import { apiRequest } from '../../../shared/api/apiClient'
import { type Recommendation, type RecommendationOperation } from '../types'

export async function getRecommendation(recommendationId: string) {
  return apiRequest<Recommendation>(`/recommendations/${recommendationId}/`)
}

/** Recommendations are now addressed by their persisted ID, not workout ID. */
export async function getPendingWorkoutRecommendation(_workoutId: string): Promise<Recommendation> {
  throw new Error('A recommendation ID is required to load a recommendation.')
}

export async function saveRecommendationOperation(recommendationId: string, operation: RecommendationOperation) {
  return apiRequest<Recommendation>(`/recommendations/${recommendationId}/operations/${operation.id}/`, { method: 'PATCH', body: JSON.stringify(operation) })
}

export async function approveRecommendationOperation(recommendationId: string, operationId: string) {
  return apiRequest<Recommendation>(`/recommendations/${recommendationId}/operations/${operationId}/accept/`, { method: 'POST' })
}

export async function rejectRecommendationOperation(recommendationId: string, operationId: string) {
  return apiRequest<Recommendation>(`/recommendations/${recommendationId}/operations/${operationId}/reject/`, { method: 'POST' })
}

export async function approveRecommendation(recommendationId: string) {
  return apiRequest<Recommendation>(`/recommendations/${recommendationId}/accept/`, { method: 'POST' })
}

export async function rejectRecommendation(recommendationId: string) {
  return apiRequest<Recommendation>(`/recommendations/${recommendationId}/reject/`, { method: 'POST' })
}

export function normalizeRecommendation(recommendation: Recommendation) { return recommendation }
