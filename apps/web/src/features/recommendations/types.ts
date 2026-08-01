export type RecommendationStatus =
  | 'pending'
  | 'applied'
  | 'rejected'
  | 'stale'
  | 'failed'

export type RecommendationOperationType =
  | 'replace_exercise'
  | 'update_exercise'
  | 'remove_exercise'
  | 'add_exercise'
  | 'move_exercise'
  | 'add_workout'
  | 'remove_workout'
  | 'update_workout'
  | 'revise_workout'

export type RecommendationOperationStatus =
  | 'pending'
  | 'accepted'
  | 'rejected'
  | 'stale'
  | 'failed'

export type RecommendationOperation = {
  id: string
  sequence: number
  operation_type: RecommendationOperationType
  status: RecommendationOperationStatus
  payload: Record<string, unknown>
  display_text: string
}

export type Recommendation = {
  id: string
  user_id: string
  workout_id: string
  snapshot_version: string
  status: RecommendationStatus
  summary: string
  reason: string
  operations: RecommendationOperation[]
  created_at: string
  updated_at: string
}
