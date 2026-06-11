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
  refreshed_at?: string
}
