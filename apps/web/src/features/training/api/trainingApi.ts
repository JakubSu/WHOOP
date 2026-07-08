import { apiRequest } from '../../../shared/api/apiClient'
import {
  type Exercise,
  type TrainingPlan,
  type WorkoutLanding,
  type Workout,
  type WorkoutExercise,
  type WorkoutListItem,
} from '../types'

export function listTrainingPlans() {
  return apiRequest<TrainingPlan[]>('/training-plans/')
}

export function listWorkouts() {
  return apiRequest<Workout[]>('/workouts/')
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

export function listWorkoutExercises() {
  return apiRequest<WorkoutExercise[]>('/workout-exercises/')
}

export function listExercises() {
  return apiRequest<Exercise[]>('/exercises/')
}
