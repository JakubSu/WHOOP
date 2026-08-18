import { ChevronRight, Clock3, Dumbbell } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { formatExpectedTime, formatWeekdayDate } from '../services/formatters'
import { type WorkoutListItem } from '../types'
import { Card } from '../../../shared/components/ui'

type WorkoutListItemButtonProps = {
  workout: WorkoutListItem
  compact?: boolean
  isTourWorkout?: boolean
}

export function WorkoutListItemButton({ workout, compact = false, isTourWorkout = false }: WorkoutListItemButtonProps) {
  const navigate = useNavigate()

  return (
    <Card className="overflow-hidden transition-colors hover:border-muted-foreground/40">
      <button
        className={compact ? 'flex w-full items-center gap-2 p-3 text-left outline-none transition-colors hover:bg-accent/40 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring' : 'flex w-full items-center gap-3 p-4 text-left outline-none transition-colors hover:bg-accent/40 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring'}
        type="button"
        data-tour={isTourWorkout ? 'created-workout' : undefined}
        onClick={() => navigate(`/workouts/${workout.id}`)}
      >
        <span className="min-w-0 flex-1">
          <strong className="block truncate text-[15px] font-semibold tracking-tight text-foreground">
            {workout.name}
          </strong>
          <span className={compact ? 'mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-muted-foreground' : 'mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground'}>
            <span className="inline-flex items-center gap-1.5">
              <Dumbbell aria-hidden="true" size={14} className="text-primary/70" />
              {workout.exercise_count} {workout.exercise_count === 1 ? 'exercise' : 'exercises'}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Clock3 aria-hidden="true" size={14} className="text-primary/70" />
              {formatExpectedTime(workout.expected_time)}
            </span>
          </span>
        </span>
        <ChevronRight aria-hidden="true" size={18} className="shrink-0 text-muted-foreground" />
        <span className="sr-only">Open {formatWeekdayDate(workout.date)} workout</span>
      </button>
    </Card>
  )
}
