import { type CoachRecommendationReference } from '../coach/types'

export type Prescription = {
  type?: 'reps' | 'time' | 'duration'
  sets?: number
  reps?: number
  seconds?: number
  weight?: string | null
  weight_unit?: string
  note?: string
}

type OperationBase = {
  id: string
  status: 'pending' | 'accepted' | 'rejected' | 'stale'
  display_text: string
  reason: string
}

export type RecommendationOperation =
  | (OperationBase & { operation_type: 'add_workout'; payload: { temporary_id: string; name: string; date: string; expected_time: number } })
  | (OperationBase & { operation_type: 'update_workout'; payload: { workout_id: string; changes: Partial<{ name: string; date: string; expected_time: number }> } })
  | (OperationBase & { operation_type: 'remove_workout'; payload: { workout_id: string } })
  | (OperationBase & { operation_type: 'add_exercise'; payload: { workout: { kind: 'existing'; workout_id: string } | { kind: 'new'; temporary_id: string }; exercise_id: string; prescription: Prescription; position: number } })
  | (OperationBase & { operation_type: 'update_exercise'; payload: { workout_exercise_id: string; target_workout_id?: string; changes?: Partial<Prescription>; position?: number } })
  | (OperationBase & { operation_type: 'remove_exercise'; payload: { workout_exercise_id: string } })

export type RecommendationGroup = {
  id: string
  title: string
  target:
    | { kind: 'existing'; workout_id: string }
    | { kind: 'new'; temporary_id: string; draft: { name: string; date: string; expected_time: number } }
  operation_ids: string[]
}

export type Recommendation = {
  id: string
  status: CoachRecommendationReference['status']
  summary: string
  groups: RecommendationGroup[]
  operations: RecommendationOperation[]
}
