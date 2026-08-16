export type CoachMessageRole = 'user' | 'assistant'
export type CoachActivityKind =
  | 'recovery_data'
  | 'training_data'
  | 'workout_data'
  | 'recommendation'
  | 'other'
export type CoachActivityStatus = 'running' | 'completed' | 'failed'

export type CoachActivity = {
  id: string
  kind: CoachActivityKind
  label: string
  status: CoachActivityStatus
}

export type CoachRecommendationSummary = {
  total: number
  pending: number
  accepted: number
  rejected: number
  stale: number
  added: number
  updated: number
  removed: number
}

export type CoachRecommendationWorkoutGroup = {
  id: string
  title: string
  operation_ids: string[]
  summary: CoachRecommendationSummary
}

export type CoachCardSnapshot = {
  version: 1
  workout_groups: CoachRecommendationWorkoutGroup[]
}

export type CoachRecommendationReference = {
  id: string
  status: 'active' | 'completed' | 'superseded' | 'expired'
  actionable: boolean
  coach_card_snapshot: CoachCardSnapshot
}

export type CoachOperation = { id: string; recommendation_id?: string; type: string; status: string }
export type CoachRecommendation = {
  id: string
  summary: string
  reason: string
  status: 'active' | 'completed' | 'superseded' | 'expired'
  groups: Array<{ id: string; title: string; operations: CoachOperation[] }>
}

export type CoachRecommendationTransition = {
  recommendation_id: string
  status: 'completed' | 'superseded' | 'expired'
  actionable: false
  replaced_by_recommendation_id?: string
}

export type CoachMessage = {
  id: string
  role: CoachMessageRole
  content: string
  created_at: string
  activities: CoachActivity[]
  recommendation: CoachRecommendationReference | null
  ui_actions: CoachUiAction[]
  /** @deprecated Message payloads no longer populate this field. */
  operations?: CoachOperation[]
}

export type CoachUiAction = {
  id: string
  type: 'exercise_resolution'
  status: 'pending' | 'resolved' | 'dismissed'
  payload: {
    requested_name: string
    draft_exercise: {
      name: string
      prescription_type: 'strength' | 'timed'
      muscle_group: string
      default_sets?: number
      default_reps?: number
      default_time?: number
      default_weight?: string | null
      default_weight_unit?: string
      notes?: string
    }
  }
  resolution: { method: 'created' | 'selected'; exercise_id: string } | null
}

export type CoachConversation = {
  id: string
  title: string | null
  created_at: string
  updated_at: string
}

export type CoachConversationSummary = {
  id: string
  title: string | null
  last_message_preview: string | null
  updated_at: string
}

export type CoachConversationPage = {
  next: string | null
  results: CoachConversationSummary[]
}

export type CoachMessagePage = {
  next: string | null
  results: CoachMessage[]
}

type StreamEnvelope = {
  version: 1
  sequence: number
  run_id: string
  conversation_id: string
  message_id: string
}

export type CoachStreamEvent =
  | { event: 'message_started'; data: StreamEnvelope }
  | {
      event: 'thinking_started'
      data: StreamEnvelope & { label: string }
    }
  | { event: 'thinking_finished'; data: StreamEnvelope }
  | {
      event: 'tool_started' | 'tool_completed' | 'tool_failed'
      data: StreamEnvelope & { activity: CoachActivity }
    }
  | {
      event: 'text_delta'
      data: StreamEnvelope & { delta: string }
    }
  | {
      event: 'completed'
      data: StreamEnvelope & {
        message: CoachMessage
        recommendation_transitions: CoachRecommendationTransition[]
        updated_messages: CoachMessage[]
      }
    }
  | {
      event: 'error'
      data: StreamEnvelope & {
        code: string
        message: string
        retryable: boolean
      }
    }
