import { apiRequest } from '../../../shared/api/apiClient'
import {
  type Exercise,
  type WorkoutLanding,
  type Workout,
  type WorkoutExercise,
  type WorkoutListPage,
} from '../types'
import { type MuscleGroup } from '../constants/muscleGroups'

export type WorkoutExerciseInput = {
  exercise: string
  sets: number
  reps: number
  time: number
  sort_order: number
  weight: string | null
  weight_unit: string
}

export type ExerciseInput = Omit<Exercise, 'id'>

type ListWorkoutsParams = {
  startDate?: string
  endDate?: string
  page?: number
  pageSize?: number
}

export function listWorkouts(params: ListWorkoutsParams = {}) {
  const query = new URLSearchParams()
  if (params.startDate) {
    query.set('startDate', params.startDate)
  }
  if (params.endDate) {
    query.set('endDate', params.endDate)
  }
  if (params.page) {
    query.set('page', String(params.page))
  }
  if (params.pageSize) {
    query.set('pageSize', String(params.pageSize))
  }

  const suffix = query.size > 0 ? `?${query.toString()}` : ''
  return apiRequest<WorkoutListPage>(`/workouts/${suffix}`)
}

export function getWorkoutLanding(today: string) {
  return apiRequest<WorkoutLanding>(`/workouts/landing/?today=${today}`)
}

export function getWorkout(workoutId: string) {
  return apiRequest<Workout>(`/workouts/${workoutId}/`)
}

export function updateWorkout(workoutId: string, input: Partial<Pick<Workout, 'name'>>) {
  return apiRequest<Workout>(`/workouts/${workoutId}/`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

export function listWorkoutExercises(workoutId: string) {
  return apiRequest<WorkoutExercise[]>(`/workouts/${workoutId}/exercises/`)
}

export function createWorkoutExercise(workoutId: string, input: WorkoutExerciseInput) {
  return apiRequest<WorkoutExercise>(`/workouts/${workoutId}/exercises/`, {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function updateWorkoutExercise(
  workoutId: string,
  workoutExerciseId: string,
  input: Partial<WorkoutExerciseInput>,
) {
  return apiRequest<WorkoutExercise>(`/workouts/${workoutId}/exercises/${workoutExerciseId}/`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

export function deleteWorkoutExercise(workoutId: string, workoutExerciseId: string) {
  return apiRequest<void>(`/workouts/${workoutId}/exercises/${workoutExerciseId}/`, {
    method: 'DELETE',
  })
}

export function listExercises(params: { muscleGroup?: MuscleGroup } = {}) {
  const query = new URLSearchParams()
  if (params.muscleGroup) {
    query.set('muscleGroup', params.muscleGroup)
  }
  const suffix = query.size > 0 ? `?${query.toString()}` : ''
  return apiRequest<Exercise[]>(`/exercises/${suffix}`)
}

export function createExercise(input: ExerciseInput) {
  return apiRequest<Exercise>('/exercises/', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}
