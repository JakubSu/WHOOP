import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo } from 'react'
import {
  getWorkout,
  getWorkoutLanding,
  listWorkouts,
  listWorkoutExercises,
  deleteWorkout,
} from '../api/trainingApi'
import {
  addDaysIso,
  buildExerciseDisplays,
  getLocalDateIso,
  getWorkoutNavigation,
  isDateToday,
} from '../services/formatters'

const WORKOUT_NAVIGATION_DAYS_BEFORE = 28
const WORKOUT_NAVIGATION_DAYS_AFTER = 28
const WORKOUT_NAVIGATION_PAGE_SIZE = 100

export function useWorkoutPage(workoutId: string | undefined) {
  const queryClient = useQueryClient()
  const today = getLocalDateIso()
  const landing = useQuery({
    queryKey: ['workout-landing', today],
    queryFn: () => getWorkoutLanding(today),
    enabled: !workoutId,
  })
  const selectedWorkout = landing.data?.selected_workout ?? null
  const resolvedWorkoutId = workoutId ?? selectedWorkout?.id
  const workout = useQuery({
    queryKey: ['workout', resolvedWorkoutId],
    queryFn: () => getWorkout(resolvedWorkoutId ?? ''),
    enabled: Boolean(resolvedWorkoutId),
  })
  const workoutExercises = useQuery({
    queryKey: ['workout-exercises', resolvedWorkoutId],
    queryFn: () => listWorkoutExercises(resolvedWorkoutId ?? ''),
    enabled: Boolean(resolvedWorkoutId),
  })

  const exerciseDisplays = useMemo(
    () => buildExerciseDisplays(workoutExercises.data ?? []),
    [workoutExercises.data],
  )
  const currentWorkout = workout.data ?? selectedWorkout
  const isToday = selectedWorkout?.is_today ?? isDateToday(currentWorkout?.date ?? null, today)
  const navigationDate = currentWorkout?.date ?? null
  const startDate = navigationDate
    ? addDaysIso(navigationDate, -WORKOUT_NAVIGATION_DAYS_BEFORE)
    : null
  const endDate = navigationDate
    ? addDaysIso(navigationDate, WORKOUT_NAVIGATION_DAYS_AFTER)
    : null
  const workouts = useQuery({
    queryKey: ['workouts', 'window', startDate, endDate],
    queryFn: () =>
      listWorkouts({
        startDate: startDate ?? undefined,
        endDate: endDate ?? undefined,
        page: 1,
        pageSize: WORKOUT_NAVIGATION_PAGE_SIZE,
      }),
    enabled: Boolean(startDate && endDate),
  })
  const navigation = getWorkoutNavigation(
    workouts.data?.results ?? [],
    resolvedWorkoutId,
  )
  const deleteMutation = useMutation({
    mutationFn: () => deleteWorkout(resolvedWorkoutId ?? ''),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['workout-landing'] }),
        queryClient.invalidateQueries({ queryKey: ['workouts'] }),
        queryClient.removeQueries({ queryKey: ['workout', resolvedWorkoutId] }),
        queryClient.removeQueries({ queryKey: ['workout-exercises', resolvedWorkoutId] }),
      ])
    },
  })

  return {
    resolvedWorkoutId,
    workout: currentWorkout,
    previousWorkout: navigation.previousWorkout,
    nextWorkout: navigation.nextWorkout,
    exerciseDisplays,
    isToday,
    deleteWorkout: () => deleteMutation.mutateAsync(),
    isDeleting: deleteMutation.isPending,
    deleteError: deleteMutation.error,
    isLoading:
      workouts.isLoading || landing.isLoading || workout.isLoading || workoutExercises.isLoading,
    error: workouts.error ?? landing.error ?? workout.error ?? workoutExercises.error,
  }
}
