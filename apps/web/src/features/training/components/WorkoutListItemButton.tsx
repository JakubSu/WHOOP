import { ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import {
  formatDate,
  formatExpectedTime,
} from '../services/formatters'
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
        <strong>{workout.name}</strong>
        <small>
          {formatDate(workout.date)} · {workout.exerciseCount} exercises ·{' '}
          {formatExpectedTime(workout.expected_time)}
        </small>
      </span>
      <ChevronRight aria-hidden="true" size={18} />
    </button>
  )
}
