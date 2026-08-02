import {
  type Exercise,
  type Workout,
  type WorkoutExercise,
  type WorkoutExerciseDisplay,
  type WorkoutListItem,
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
  return dateToIso(date)
}

export function getWeekStartIso(value: string) {
  const date = new Date(`${value}T00:00:00`)
  const daysSinceMonday = (date.getDay() + 6) % 7
  date.setDate(date.getDate() - daysSinceMonday)
  return dateToIso(date)
}

export function getWeekEndIso(value: string) {
  return addDaysIso(getWeekStartIso(value), 6)
}

export function getWeekDates(value: string) {
  const startDate = getWeekStartIso(value)
  return Array.from({ length: 7 }, (_, index) => addDaysIso(startDate, index))
}

export function getWeekWindowRange(weekStartDate: string, weeksBefore = 2, weeksAfter = 2) {
  return {
    startDate: addDaysIso(weekStartDate, -7 * weeksBefore),
    endDate: addDaysIso(weekStartDate, 6 + 7 * weeksAfter),
  }
}

export function formatWeekRange(weekStartDate: string) {
  const startDate = new Date(`${getWeekStartIso(weekStartDate)}T00:00:00`)
  const endDate = new Date(`${getWeekEndIso(weekStartDate)}T00:00:00`)
  const monthDayFormatter = new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
  })
  const dayFormatter = new Intl.DateTimeFormat('en-US', { day: 'numeric' })

  if (startDate.getFullYear() === endDate.getFullYear() && startDate.getMonth() === endDate.getMonth()) {
    return `${monthDayFormatter.format(startDate)} - ${dayFormatter.format(endDate)}`
  }

  return `${monthDayFormatter.format(startDate)} - ${monthDayFormatter.format(endDate)}`
}

export function groupWorkoutsByDate(workouts: WorkoutListItem[]) {
  return workouts.reduce<Record<string, WorkoutListItem[]>>((groupedWorkouts, workout) => {
    if (!workout.date) {
      return groupedWorkouts
    }

    const dateWorkouts = groupedWorkouts[workout.date] ?? []
    return {
      ...groupedWorkouts,
      [workout.date]: [...dateWorkouts, workout],
    }
  }, {})
}

function dateToIso(date: Date) {
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
