import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listWorkouts } from '../api/trainingApi'
import {
  addDaysIso,
  formatWeekRange,
  getLocalDateIso,
  getWeekDates,
  getWeekStartIso,
  getWeekWindowRange,
  groupWorkoutsByDate,
} from '../services/formatters'
import { useAuthStore } from '../../auth/store/authStore'

const WEEK_WINDOW_WEEKS_BEFORE = 2
const WEEK_WINDOW_WEEKS_AFTER = 2
const WEEK_WINDOW_PAGE_SIZE = 200

const weekdayLabels = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']

export function useWeekPage(anchorDate?: string | null) {
  const userId = useAuthStore((state) => state.user?.id)
  const initialWeekStartDate = getWeekStartIso(anchorDate || getLocalDateIso())
  const [visibleWeekStartDate, setVisibleWeekStartDate] = useState(initialWeekStartDate)
  const [windowCenterWeekStartDate, setWindowCenterWeekStartDate] = useState(
    initialWeekStartDate,
  )
  const weekWindow = getWeekWindowRange(
    windowCenterWeekStartDate,
    WEEK_WINDOW_WEEKS_BEFORE,
    WEEK_WINDOW_WEEKS_AFTER,
  )
  const firstCachedWeekStartDate = weekWindow.startDate
  const lastCachedWeekStartDate = addDaysIso(
    windowCenterWeekStartDate,
    7 * WEEK_WINDOW_WEEKS_AFTER,
  )
  const workouts = useQuery({
    queryKey: ['workouts', userId, 'week-window', weekWindow.startDate, weekWindow.endDate],
    queryFn: () =>
      listWorkouts({
        startDate: weekWindow.startDate,
        endDate: weekWindow.endDate,
        page: 1,
        pageSize: WEEK_WINDOW_PAGE_SIZE,
    }),
    enabled: Boolean(userId),
  })
  const workoutsByDate = useMemo(
    () => groupWorkoutsByDate(workouts.data?.results ?? []),
    [workouts.data?.results],
  )
  const weekDays = getWeekDates(visibleWeekStartDate).map((date, index) => ({
    date,
    label: weekdayLabels[index],
    workouts: workoutsByDate[date] ?? [],
  }))

  function moveWeek(direction: -1 | 1) {
    const nextWeekStartDate = addDaysIso(visibleWeekStartDate, direction * 7)
    setVisibleWeekStartDate(nextWeekStartDate)

    if (
      nextWeekStartDate < firstCachedWeekStartDate ||
      nextWeekStartDate > lastCachedWeekStartDate
    ) {
      setWindowCenterWeekStartDate(nextWeekStartDate)
    }
  }

  return {
    visibleWeekStartDate,
    rangeTitle: formatWeekRange(visibleWeekStartDate),
    weekDays,
    moveToPreviousWeek: () => moveWeek(-1),
    moveToNextWeek: () => moveWeek(1),
    isLoading: workouts.isLoading,
    error: workouts.error,
  }
}
