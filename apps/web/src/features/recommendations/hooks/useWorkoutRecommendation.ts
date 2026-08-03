import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { listExercises } from '../../training/api/trainingApi'
import { type Exercise, type ExerciseSummary, type WorkoutExercise } from '../../training/types'
import { approveRecommendationOperation, rejectRecommendationOperation, saveRecommendationOperation } from '../api/recommendationApi'
import { type Recommendation, type RecommendationOperation } from '../types'

export function useWorkoutRecommendation(workoutId: string | undefined) {
  const client = useQueryClient()
  const key = ['recommendation', workoutId] as const
  const recommendation = useQuery<Recommendation | null>({ queryKey: key, queryFn: async () => null, enabled: false })
  const library = useQuery({ queryKey: ['exercises'], queryFn: listExercises })
  const save = useMutation({ mutationFn: (operation: RecommendationOperation) => saveRecommendationOperation(recommendation.data?.id ?? '', operation), onSuccess: (next) => client.setQueryData(key, next) })
  const accept = useMutation({
    mutationFn: (operationId: string) => approveRecommendationOperation(recommendation.data?.id ?? '', operationId),
    onSuccess: (next, id) => {
      const operation = recommendation.data?.operations.find((item) => item.id === id)
      if (operation) client.setQueryData<WorkoutExercise[]>(['workout-exercises', workoutId], (rows) => apply(rows ?? [], operation, library.data ?? []))
      client.setQueryData(key, next)
    },
  })
  const reject = useMutation({ mutationFn: (operationId: string) => rejectRecommendationOperation(recommendation.data?.id ?? '', operationId), onSuccess: (next) => client.setQueryData(key, next) })
  return { recommendation: recommendation.data ?? null, exerciseLibrary: library.data ?? [], saveOperation: (operation: RecommendationOperation) => save.mutate(operation), acceptOperation: (id: string) => accept.mutate(id), rejectOperation: (id: string) => reject.mutate(id), savingOperationId: save.isPending ? save.variables.id : null, acceptingOperationId: accept.isPending ? accept.variables : null, rejectingOperationId: reject.isPending ? reject.variables : null, isLoading: recommendation.isLoading, error: recommendation.error ?? library.error ?? save.error ?? accept.error ?? reject.error }
}

function apply(rows: WorkoutExercise[], operation: RecommendationOperation, library: Exercise[]) {
  if (operation.operation_type === 'add_exercise') {
    const added: WorkoutExercise = { id: `mock-${crypto.randomUUID()}`, workout: rows[0]?.workout ?? '', exercise: summary(operation.payload.exercise.id, operation.payload.exercise.name, library), sort_order: 1, ...operation.payload.prescription }
    return insert(rows, added, operation.payload.position)
  }
  const index = targetIndex(rows, operation.payload.workout_exercise_id)
  if (operation.operation_type === 'remove_exercise') return renumber(rows.filter((_, rowIndex) => rowIndex !== index))
  const changed = rows.map((row, rowIndex) => rowIndex === index ? { ...row, ...operation.payload.changes } : row)
  if (!operation.payload.position) return changed
  const moved = changed[index]
  return moved ? insert(changed.filter((_, rowIndex) => rowIndex !== index), moved, operation.payload.position) : changed
}
function insert(rows: WorkoutExercise[], row: WorkoutExercise, position: number) { const next = [...rows]; next.splice(Math.max(0, Math.min(rows.length, position - 1)), 0, row); return renumber(next) }
function renumber(rows: WorkoutExercise[]) { return rows.map((row, index) => ({ ...row, sort_order: index + 1 })) }
function targetIndex(rows: WorkoutExercise[], id: string) { const found = rows.findIndex((row) => row.id === id); if (found >= 0) return found; if (id === 'first-exercise') return 0; if (id === 'second-exercise') return Math.min(1, rows.length - 1); return rows.length - 1 }
function summary(id: string, name: string, library: Exercise[]): ExerciseSummary { const match = library.find((exercise) => exercise.id === id); return { id, name, prescription_type: match?.prescription_type ?? 'strength', muscle_group: match?.muscle_group ?? '' } }
