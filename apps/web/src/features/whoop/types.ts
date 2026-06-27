export type WhoopRecentWorkout = {
  id: string
  sport_name: string
  start: string
  end: string
  duration_minutes: number
  strain?: number | null
  average_heart_rate?: number | null
  max_heart_rate?: number | null
  kilojoule?: number | null
  distance_meter?: number | null
  score_state: string
}

export type WhoopSummary = {
  connected: boolean
  detail?: string
  snapshot_date?: string
  recovery_score?: number | null
  sleep_performance_percent?: number | null
  day_strain?: number | null
  hrv_rmssd_milli?: number | null
  resting_heart_rate?: number | null
  sleep_duration_minutes?: number | null
  recent_workout_count?: number
  recent_workouts?: WhoopRecentWorkout[]
  refreshed_at?: string
}
