import { apiRequest } from '../../../shared/api/apiClient'
import {
  type Exercise,
  type TrainingPlan,
  type Workout,
  type WorkoutExercise,
} from '../types'

export function listTrainingPlans() {
  return apiRequest<TrainingPlan[]>('/training-plans/')
}

export function listWorkouts() {
  return apiRequest<Workout[]>('/workouts/')
}

export function getWorkout(workoutId: string) {
  return apiRequest<Workout>(`/workouts/${workoutId}/`)
}

export function listWorkoutExercises() {
  return apiRequest<WorkoutExercise[]>('/workout-exercises/')
}

export function listExercises() {
  return apiRequest<Exercise[]>('/exercises/')
}
