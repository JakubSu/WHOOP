import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button, Spinner } from '../../../shared/components/ui'
import { WorkoutListItemButton } from './WorkoutListItemButton'
import { formatDate } from '../services/formatters'
import { useWeekPage } from '../hooks/useWeekPage'
import { useCoachPageContext } from '../../coach/context/CoachOverlayContext'

type WeekPlanListProps = {
  date?: string | null
  compact?: boolean
}

export function WeekPlanList({ date, compact = false }: WeekPlanListProps) {
  const { visibleWeekStartDate, rangeTitle, weekDays, moveToPreviousWeek, moveToNextWeek, isLoading, error } = useWeekPage(date)

  return (
    <section className={compact ? 'grid min-h-0 grid-rows-[auto_1fr]' : ''} data-tour={compact ? undefined : 'week-navigation-page'} data-tour-workspace-ready={!isLoading && !compact ? 'true' : undefined}>
      {!compact ? <WeekCoachContext weekStartDate={visibleWeekStartDate} /> : null}
      <header className={compact ? 'mb-3' : 'mb-6 border-b border-border pb-5'}>
        {!compact ? <p className="text-xs font-bold uppercase tracking-[0.16em] text-primary">Week</p> : null}
        <div className={compact ? 'grid grid-cols-[2rem_minmax(0,1fr)_2rem] items-center gap-1' : 'mt-2 grid grid-cols-[2.5rem_minmax(0,1fr)_2.5rem] items-center gap-2'}>
          <Button type="button" variant="ghost" size="icon" className={compact ? 'size-8' : undefined} aria-label="Previous week" onClick={moveToPreviousWeek}>
            <ChevronLeft aria-hidden="true" size={compact ? 18 : 21} />
          </Button>
          <div className="min-w-0 text-center">
            {compact ? <p className="truncate text-sm font-bold text-foreground">{rangeTitle}</p> : <h1 className="truncate text-2xl font-bold tracking-tight text-foreground sm:text-3xl">{rangeTitle}</h1>}
            {!compact ? <p className="mt-1 text-sm text-muted-foreground">Your scheduled training</p> : null}
          </div>
          <Button type="button" variant="ghost" size="icon" className={compact ? 'size-8' : undefined} aria-label="Next week" onClick={moveToNextWeek}>
            <ChevronRight aria-hidden="true" size={compact ? 18 : 21} />
          </Button>
        </div>
      </header>
      <div className={compact ? 'min-h-0 overflow-y-auto pr-1' : ''}>
        {isLoading ? <p className="mb-4 flex items-center gap-2 text-sm text-muted-foreground"><Spinner className="size-4" /> Loading week...</p> : null}
        {error ? <p role="alert" className="mb-4 text-sm text-destructive">Could not load this week.</p> : null}
        <div className="grid gap-3">
          {weekDays.map((day) => (
            <section key={day.date}>
              <div className="mb-2 flex items-baseline justify-between gap-3 px-1">
                <strong className="text-sm font-semibold text-foreground">{day.label}</strong>
                <span className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">{formatDate(day.date)}</span>
              </div>
              <div className="grid gap-2">
                {day.workouts.length ? day.workouts.map((workout) => <WorkoutListItemButton key={workout.id} workout={workout} compact={compact} />) : (
                  <p className="rounded-lg border border-dashed border-border px-3 py-2 text-sm text-muted-foreground">Rest day</p>
                )}
              </div>
            </section>
          ))}
        </div>
      </div>
    </section>
  )
}

function WeekCoachContext({ weekStartDate }: { weekStartDate: string }) {
  useCoachPageContext({ kind: 'week', week_start_date: weekStartDate })
  return null
}
