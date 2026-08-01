export type TrainingPlan = {
  id: string
  name: string
  start_date: string | null
  end_date: string | null
}

export type Workout = {
  id: string
  plan: string | null
  name: string
  date: string | null
  expected_time: number | null
}

export type WorkoutLandingSelection = Workout & {
  is_today: boolean
}

export type WorkoutLanding = {
  has_workout_today: boolean
  message: string | null
  selected_workout: WorkoutLandingSelection | null
}

export type WorkoutExercise = {
  id: string
  workout: string
  exercise: string | ExerciseSummary
  sets: number
  reps: number
  time: number
  sort_order: number
  weight: string | null
  weight_unit: string
  note: string
}

export type ExerciseSummary = {
  id: string
  name: string
  prescription_type: 'strength' | 'timed'
  muscle_group: string
}

export type Exercise = {
  id: string
  name: string
  prescription_type: 'strength' | 'timed'
  default_sets: number
  default_reps: number
  muscle_group: string
  default_time: number
  notes: string
}

export type WorkoutListItem = Workout & {
  exercise_count: number
}

export type WorkoutListPage = {
  count: number
  page: number
  page_size: number
  results: Workout[]
}

export type WorkoutExerciseDisplay = WorkoutExercise & {
  exerciseName: string
  prescription: string
}
