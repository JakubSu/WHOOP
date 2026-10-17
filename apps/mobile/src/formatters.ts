import type { WorkoutExercise } from './types'

export function localDateIso(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function formatToday(date = new Date()) {
  return new Intl.DateTimeFormat(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  }).format(date)
}

export function formatPrescription(exercise: WorkoutExercise) {
  const name = typeof exercise.exercise === 'string' ? 'Exercise' : exercise.exercise.name
  const weight = exercise.weight ? ` · ${exercise.weight} ${exercise.weight_unit || 'lb'}` : ''
  const prescription = exercise.time > 0
    ? `${exercise.sets > 0 ? `${exercise.sets} × ` : ''}${exercise.time} sec`
    : exercise.sets > 0 && exercise.reps > 0
      ? `${exercise.sets} sets × ${exercise.reps} reps${weight}`
      : 'Details TBD'
  return { name, prescription }
}

export function formatRefreshedAt(value?: string) {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return `Updated ${new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(date)}`
}
