import { ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { formatExpectedTime, formatWeekdayDate } from '../services/formatters'
import { type WorkoutListItem } from '../types'

type WorkoutListItemButtonProps = {
  workout: WorkoutListItem
}

export function WorkoutListItemButton({ workout }: WorkoutListItemButtonProps) {
  const navigate = useNavigate()

  return (
    <button
      className="workout-row"
      type="button"
      onClick={() => navigate(`/workouts/${workout.id}`)}
    >
      <span>
        <strong>{formatWeekdayDate(workout.date)}</strong>
        <small>
          {workout.name} | {workout.exercise_count} exercises |{' '}
          {formatExpectedTime(workout.expected_time)}
        </small>
      </span>
      <ChevronRight aria-hidden="true" size={18} />
    </button>
  )
}
