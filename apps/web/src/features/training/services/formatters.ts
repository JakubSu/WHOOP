import {
  type Exercise,
  type WorkoutExercise,
  type WorkoutExerciseDisplay,
} from '../types'

export function formatDate(value: string | null) {
  if (!value) {
    return 'No date'
  }

  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
  }).format(new Date(`${value}T00:00:00`))
}

export function formatWeekdayDate(value: string | null) {
  if (!value) {
    return 'No date'
  }

  return new Intl.DateTimeFormat(undefined, {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  }).format(new Date(`${value}T00:00:00`))
}

export function getLocalDateIso() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function isDateToday(value: string | null, today = getLocalDateIso()) {
  return Boolean(value) && value === today
}

export function getWorkoutScreenTitle(value: string | null, isToday: boolean) {
  return isToday ? 'Today' : formatDate(value)
}

export function getWorkoutScreenEyebrow(message: string | null) {
  return message ?? 'Workout'
}

export function formatExpectedTime(minutes: number | null) {
  if (!minutes) {
    return 'Time TBD'
  }

  return `${minutes} min`
}

export function buildExerciseDisplays(
  workoutExercises: WorkoutExercise[],
  exercises: Exercise[],
): WorkoutExerciseDisplay[] {
  const exerciseById = new Map(exercises.map((exercise) => [exercise.id, exercise]))

  return workoutExercises.map((workoutExercise) => {
    const exercise = exerciseById.get(workoutExercise.exercise)
    return {
      ...workoutExercise,
      exerciseName: exercise?.name ?? 'Exercise',
      prescription: formatPrescription(workoutExercise),
    }
  })
}

export function formatPrescription(workoutExercise: WorkoutExercise) {
  const weight = formatWeight(workoutExercise)
  const strength = [workoutExercise.sets, workoutExercise.reps].every(
    (value) => value > 0,
  )

  if (strength) {
    const base = `${workoutExercise.sets} sets x ${workoutExercise.reps} reps`
    return weight ? `${base} @ ${weight}` : base
  }

  if (workoutExercise.time > 0) {
    return `${workoutExercise.time} sec`
  }

  return weight ? `Weight: ${weight}` : 'Details TBD'
}

function formatWeight(workoutExercise: WorkoutExercise) {
  if (!workoutExercise.weight) {
    return ''
  }

  const amount = Number(workoutExercise.weight)
  const displayAmount = Number.isFinite(amount)
    ? amount.toLocaleString(undefined, { maximumFractionDigits: 2 })
    : workoutExercise.weight
  return `${displayAmount} ${workoutExercise.weight_unit || 'lb'}`
}
