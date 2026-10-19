export type UserProfile = {
  id: string
  email: string
  display_name: string
  whoop_connection_allowed?: boolean
}

export type AuthSession = {
  user: UserProfile
  access: string
  refresh?: string
}

export type WhoopSummary = {
  connected: boolean
  detail?: string
  snapshot_date?: string
  recovery_score?: number | null
  sleep_performance_percent?: number | null
  day_strain?: number | null
  sleep_duration_minutes?: number | null
  refreshed_at?: string
}

export type WorkoutLanding = {
  has_workout_today: boolean
  message: string | null
  selected_workout: (Workout & { is_today: boolean }) | null
}

export type Workout = {
  id: string
  name: string
  date: string | null
  expected_time: number | null
  plan?: string | null
}

export type ExerciseSummary = {
  id: string
  name: string
  prescription_type: 'strength' | 'timed_sets' | 'timed'
}

export type WorkoutExercise = {
  id: string
  exercise: string | ExerciseSummary
  sets: number
  reps: number
  time: number
  weight: string | null
  weight_unit: string
  sort_order: number
}

export type WhoopAccessRequest = {
  status: 'none' | 'pending' | 'approved' | 'rejected'
}
