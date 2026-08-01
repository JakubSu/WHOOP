import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { getErrorMessage } from '../../../shared/api/errors'
import { InlineError } from '../../../shared/components/InlineError'
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
      <section className="training-content week-content">
        <div className="section-heading">
          <p className="eyebrow">Week</p>
          <div className="workout-title-nav">
            <button
              className="workout-nav-button"
              type="button"
              aria-label="Previous week"
              onClick={moveToPreviousWeek}
            >
              <ChevronLeft aria-hidden="true" size={21} />
            </button>
            <div className="workout-title-nav__title">
              <h1>{rangeTitle}</h1>
            </div>
            <button
              className="workout-nav-button"
              type="button"
              aria-label="Next week"
              onClick={moveToNextWeek}
            >
              <ChevronRight aria-hidden="true" size={21} />
            </button>
          </div>
        </div>
        <div className="workout-status-stack">
          {isLoading ? <p className="muted">Loading week...</p> : null}
          <InlineError message={error ? getErrorMessage(error) : null} />
        </div>
        <ScrollableStack
          empty={
            !isLoading ? (
              <p className="empty-state">No workouts scheduled this week.</p>
            ) : null
          }
        >
          {weekDays.map((day) => (
            <section className="week-day" key={day.date}>
              <div className="week-day__heading">
                <strong>{day.label}</strong>
                <span>{formatDate(day.date)}</span>
              </div>
              <div className="week-day__workouts">
                {day.workouts.length > 0 ? (
                  day.workouts.map((workout) => (
                    <WorkoutListItemButton key={workout.id} workout={workout} />
                  ))
                ) : (
                  <p className="week-day__empty">No workout</p>
                )}
              </div>
            </section>
          ))}
        </ScrollableStack>
      </section>
    </TrainingLayout>
  )
}
