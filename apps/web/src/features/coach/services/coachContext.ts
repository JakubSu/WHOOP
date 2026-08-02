import { matchPath } from 'react-router-dom'

export type CoachPageType =
  | 'today_workout'
  | 'workout'
  | 'recovery'

export type CoachPageContext = {
  page_type: CoachPageType
  context_id: string
}

export function coachContextKey(context: CoachPageContext) {
  return `${context.page_type}:${context.context_id}`
}

export function areCoachContextsEqual(
  first: CoachPageContext | null,
  second: CoachPageContext | null,
) {
  if (!first || !second) {
    return first === second
  }

  return coachContextKey(first) === coachContextKey(second)
}

export function labelForCoachContext(context: CoachPageContext | null) {
  if (!context) {
    return 'Coach'
  }

  if (context.page_type === 'today_workout') {
    return 'Today'
  }
  if (context.page_type === 'recovery') {
    return 'Recovery'
  }

  return 'Workout'
}

export function getCoachPageContextForRoute(pathname: string): CoachPageContext | null {
  if (pathname === '/training') {
    return {
      page_type: 'today_workout',
      context_id: '',
    }
  }

  const workoutMatch = matchPath('/workouts/:workoutId', pathname)
  const workoutId = workoutMatch?.params.workoutId
  if (workoutId) {
    return {
      page_type: 'workout',
      context_id: workoutId,
    }
  }

  return null
}
