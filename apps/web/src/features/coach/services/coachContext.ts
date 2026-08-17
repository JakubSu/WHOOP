import { matchPath } from 'react-router-dom'

export type CoachViewContext =
  | { kind: 'workout'; workout_id: string }
  | { kind: 'week'; week_start_date: string }

export function coachContextKey(context: CoachViewContext) {
  return context.kind === 'workout'
    ? `workout:${context.workout_id}`
    : `week:${context.week_start_date}`
}

export function areCoachContextsEqual(
  first: CoachViewContext | null,
  second: CoachViewContext | null,
) {
  if (!first || !second) {
    return first === second
  }

  return coachContextKey(first) === coachContextKey(second)
}

export function labelForCoachContext(context: CoachViewContext | null) {
  if (!context) {
    return 'Coach'
  }

  return context.kind === 'week' ? 'Week' : 'Workout'
}

export function getCoachPageContextForRoute(pathname: string): CoachViewContext | null {
  const workoutMatch = matchPath('/workouts/:workoutId', pathname)
  const workoutId = workoutMatch?.params.workoutId
  if (workoutId) {
    return {
      kind: 'workout',
      workout_id: workoutId,
    }
  }

  return null
}
