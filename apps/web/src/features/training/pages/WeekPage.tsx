import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { getErrorMessage } from '../../../shared/api/errors'
import { InlineError } from '../../../shared/components/InlineError'
import { Button, Spinner } from '../../../shared/components/ui'
import { ScrollableStack } from '../../../shared/layout/ScrollableStack'
import { TrainingLayout } from '../../../shared/layout/TrainingLayout'
import { useCoachPageContext } from '../../coach/context/CoachOverlayContext'
import { WorkoutListItemButton } from '../components/WorkoutListItemButton'
import { formatDate } from '../services/formatters'
import { useWeekPage } from '../hooks/useWeekPage'

export function WeekPage() {
  const [searchParams] = useSearchParams()
  const {
    rangeTitle,
    weekDays,
    moveToPreviousWeek,
    moveToNextWeek,
    isLoading,
    error,
  } = useWeekPage(searchParams.get('date'))
  useCoachPageContext(null)

  return (
    <TrainingLayout>
      <section className="mx-auto w-full max-w-2xl px-4 py-6 sm:px-6">
        <header className="mb-6 border-b border-border pb-5">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-primary">Week</p>
          <div className="mt-2 grid grid-cols-[2.5rem_minmax(0,1fr)_2.5rem] items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Previous week"
              onClick={moveToPreviousWeek}
            >
              <ChevronLeft aria-hidden="true" size={21} />
            </Button>
            <div className="min-w-0 text-center">
              <h1 className="truncate text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                {rangeTitle}
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">Your scheduled training</p>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Next week"
              onClick={moveToNextWeek}
            >
              <ChevronRight aria-hidden="true" size={21} />
            </Button>
          </div>
        </header>
        <div className="mb-4">
          {isLoading ? (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Spinner className="size-4" /> Loading week...
            </p>
          ) : null}
          <InlineError message={error ? getErrorMessage(error) : null} />
        </div>
        <ScrollableStack
          empty={
            !isLoading ? (
              <p className="rounded-lg border border-dashed border-border px-4 py-8 text-center text-sm text-muted-foreground">
                No workouts scheduled this week.
              </p>
            ) : null
          }
        >
          {weekDays.map((day) => (
            <section key={day.date}>
              <div className="mb-2 flex items-baseline justify-between gap-3 px-1">
                <strong className="text-sm font-semibold text-foreground">{day.label}</strong>
                <span className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
                  {formatDate(day.date)}
                </span>
              </div>
              <div className="grid gap-2">
                {day.workouts.length > 0 ? (
                  day.workouts.map((workout) => (
                    <WorkoutListItemButton key={workout.id} workout={workout} />
                  ))
                ) : (
                  <p className="rounded-lg border border-dashed border-border px-4 py-3 text-sm text-muted-foreground">
                    Rest day
                  </p>
                )}
              </div>
            </section>
          ))}
        </ScrollableStack>
      </section>
    </TrainingLayout>
  )
}
