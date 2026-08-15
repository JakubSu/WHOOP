import { type Exercise, type WorkoutExerciseDisplay } from '../../training/types'
import { type RecommendationGroup, type RecommendationOperation } from '../types'

export function groupTargetKey(group: RecommendationGroup) {
  return group.target.kind === 'existing'
    ? group.target.workout_id
    : group.target.temporary_id
}

export function existingWorkoutIds(groups: RecommendationGroup[]) {
  return groups.flatMap((group) =>
    group.target.kind === 'existing' ? [group.target.workout_id] : [],
  )
}

export function buildDraftExercises(
  operations: RecommendationOperation[],
  library: Exercise[],
): WorkoutExerciseDisplay[] {
  return operations
    .filter((operation): operation is Extract<RecommendationOperation, { operation_type: 'add_exercise' }> => operation.operation_type === 'add_exercise')
    .map((operation) => {
      const exercise = library.find((item) => item.id === operation.payload.exercise_id)
      const prescription = operation.payload.prescription
      const exerciseName = exercise?.name ?? operation.display_text
      const reps = prescription.reps ?? 0
      const time = prescription.seconds ?? 0
      return {
        id: operation.id,
        workout: '',
        exercise: { id: operation.payload.exercise_id, name: exerciseName, muscle_group: exercise?.muscle_group ?? 'other', prescription_type: exercise?.prescription_type ?? (prescription.type === 'time' ? 'timed' : 'strength') },
        exerciseName,
        sets: prescription.sets,
        reps,
        time,
        sort_order: operation.payload.position,
        weight: prescription.weight ?? null,
        weight_unit: prescription.weight_unit ?? 'lb',
        note: prescription.note ?? '',
        prescription: prescription.type === 'time' ? `${prescription.sets} × ${time}s` : `${prescription.sets} × ${reps}`,
      }
    })
    .sort((left, right) => left.sort_order - right.sort_order)
}
