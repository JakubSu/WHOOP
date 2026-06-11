import { type WorkoutExerciseDisplay } from '../types'

type ExerciseCardProps = {
  exercise: WorkoutExerciseDisplay
}

export function ExerciseCard({ exercise }: ExerciseCardProps) {
  return (
    <article className="exercise-card">
      <strong>{exercise.exerciseName}</strong>
      <span>{exercise.prescription}</span>
      {exercise.note ? <small>{exercise.note}</small> : null}
    </article>
  )
}
