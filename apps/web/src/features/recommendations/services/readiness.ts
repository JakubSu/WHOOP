import { type Recommendation } from '../types'

const resolvedOperationStatuses = new Set(['accepted', 'rejected'])

export function isRecommendationReadyToSave(
  recommendation: Recommendation | null,
) {
  if (!recommendation) {
    return false
  }

  return (
    recommendation.operations.length > 0 &&
    recommendation.operations.every((operation) =>
      resolvedOperationStatuses.has(operation.status),
    )
  )
}
