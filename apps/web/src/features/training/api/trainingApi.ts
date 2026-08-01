import { apiRequest } from '../../../shared/api/apiClient'
import {
  type Exercise,
  type TrainingPlan,
  type WorkoutLanding,
  type Workout,
  type WorkoutExercise,
  type WorkoutListPage,
  type WorkoutListItem,
} from '../types'

type ListWorkoutsParams = {
  startDate?: string
  endDate?: string
  page?: number
  pageSize?: number
}

export function listTrainingPlans() {
  return apiRequest<TrainingPlan[]>('/training-plans/')
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

export function listTrainingPlanWorkouts(planId: string) {
  return apiRequest<WorkoutListItem[]>(`/training-plans/${planId}/workouts/`)
}

export function listWorkoutExercises(workoutId: string) {
  return apiRequest<WorkoutExercise[]>(`/workouts/${workoutId}/exercises/`)
}

export function listExercises() {
  return apiRequest<Exercise[]>('/exercises/')
}
