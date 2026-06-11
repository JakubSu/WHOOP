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

export type WorkoutExercise = {
  id: string
  workout: string
  exercise: string
  sets: number
  reps: number
  time: number
  weight: string | null
  weight_unit: string
  note: string
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
  exerciseCount: number
}

export type WorkoutExerciseDisplay = WorkoutExercise & {
  exerciseName: string
  prescription: string
}
