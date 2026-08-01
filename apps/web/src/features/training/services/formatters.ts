import {
  type Exercise,
  type Workout,
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

export function addDaysIso(value: string, days: number) {
  const date = new Date(`${value}T00:00:00`)
  date.setDate(date.getDate() + days)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function isDateToday(value: string | null, today = getLocalDateIso()) {
  return Boolean(value) && value === today
}

export function getWorkoutScreenTitle(value: string | null, isToday: boolean) {
  return isToday ? 'Today' : formatDate(value)
}

export function formatExpectedTime(minutes: number | null) {
  if (!minutes) {
    return 'Time TBD'
  }

  return `${minutes} min`
}

export function getWorkoutNavigation(
  workouts: Workout[],
  currentWorkoutId: string | undefined,
) {
  const orderedWorkouts = [...workouts].sort(compareWorkoutsByDate)
  const currentIndex = orderedWorkouts.findIndex(
    (item) => item.id === currentWorkoutId,
  )

  if (currentIndex === -1) {
    return {
      previousWorkout: null,
      nextWorkout: null,
    }
  }

  return {
    previousWorkout: orderedWorkouts[currentIndex - 1] ?? null,
    nextWorkout: orderedWorkouts[currentIndex + 1] ?? null,
  }
}

export function buildExerciseDisplays(
  workoutExercises: WorkoutExercise[],
  exercises: Exercise[] = [],
): WorkoutExerciseDisplay[] {
  const exerciseById = new Map(exercises.map((exercise) => [exercise.id, exercise]))

  return workoutExercises.map((workoutExercise) => {
    const exercise =
      typeof workoutExercise.exercise === 'string'
        ? exerciseById.get(workoutExercise.exercise)
        : workoutExercise.exercise
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

function compareWorkoutsByDate(left: Workout, right: Workout) {
  return (
    compareNullableStrings(left.date, right.date) ||
    left.name.localeCompare(right.name) ||
    left.id.localeCompare(right.id)
  )
}

function compareNullableStrings(left: string | null, right: string | null) {
  if (left === right) {
    return 0
  }
  if (left === null) {
    return 1
  }
  if (right === null) {
    return -1
  }
  return left.localeCompare(right)
}
