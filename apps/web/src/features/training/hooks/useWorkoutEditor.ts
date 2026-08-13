import { arrayMove } from '@dnd-kit/sortable'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import {
  createExercise,
  createWorkoutExercise,
  deleteWorkoutExercise,
  listExercises,
  type ExerciseInput,
  type WorkoutExerciseInput,
  updateWorkout,
  updateWorkoutExercise,
} from '../api/trainingApi'
import { type Exercise, type WorkoutExerciseDisplay } from '../types'
import { type ExerciseValues } from '../components/AddExerciseDialog'
import { type MuscleGroup } from '../constants/muscleGroups'

export type DraftExercise = WorkoutExerciseDisplay & { isNew?: boolean }

export function useWorkoutEditor(
  workoutId: string | undefined,
  exercises: WorkoutExerciseDisplay[],
  workoutName: string | undefined,
) {
  const queryClient = useQueryClient()
  const [isEditing, setIsEditing] = useState(false)
  const [draftExercises, setDraftExercises] = useState<DraftExercise[]>([])
  const [originalExercises, setOriginalExercises] = useState<DraftExercise[]>([])
  const [isAddOpen, setIsAddOpen] = useState(false)
  const [muscleGroupFilter, setMuscleGroupFilter] = useState<MuscleGroup | undefined>()
  const [draftWorkoutName, setDraftWorkoutName] = useState(workoutName ?? '')
  const [originalWorkoutName, setOriginalWorkoutName] = useState(workoutName ?? '')
  const exerciseLibrary = useQuery({
    queryKey: ['exercises', muscleGroupFilter],
    queryFn: () => listExercises({ muscleGroup: muscleGroupFilter }),
    enabled: isEditing,
  })
  const createExerciseMutation = useMutation({
    mutationFn: createExercise,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['exercises'] })
    },
  })

  useEffect(() => {
    if (!isEditing) {
      setDraftExercises(exercises)
      setOriginalExercises(exercises)
      setDraftWorkoutName(workoutName ?? '')
      setOriginalWorkoutName(workoutName ?? '')
    }
  }, [exercises, isEditing, workoutName])

  useEffect(() => {
    setIsEditing(false)
    setIsAddOpen(false)
  }, [workoutId])

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!workoutId) return

      if (draftWorkoutName !== originalWorkoutName) {
        await updateWorkout(workoutId, { name: draftWorkoutName })
      }

      const originalIds = new Set(originalExercises.map((exercise) => exercise.id))
      const draftIds = new Set(
        draftExercises
          .filter((exercise) => !exercise.isNew)
          .map((exercise) => exercise.id),
      )

      await Promise.all(
        originalExercises
          .filter((exercise) => !draftIds.has(exercise.id))
          .map((exercise) => deleteWorkoutExercise(workoutId, exercise.id)),
      )

      for (const [sortOrder, exercise] of draftExercises.entries()) {
        const input = toWorkoutExerciseInput(exercise, sortOrder)
        if (exercise.isNew || !originalIds.has(exercise.id)) {
          await createWorkoutExercise(workoutId, input)
        } else {
          await updateWorkoutExercise(workoutId, exercise.id, input)
        }
      }
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['workout', workoutId] }),
        queryClient.invalidateQueries({ queryKey: ['workout-exercises', workoutId] }),
        queryClient.invalidateQueries({ queryKey: ['workouts'] }),
      ])
      setIsEditing(false)
    },
  })

  function startEditing() {
    setDraftExercises(exercises)
    setOriginalExercises(exercises)
    setDraftWorkoutName(workoutName ?? '')
    setOriginalWorkoutName(workoutName ?? '')
    setIsEditing(true)
  }

  function cancelEditing() {
    setDraftExercises(originalExercises)
    setDraftWorkoutName(originalWorkoutName)
    setIsEditing(false)
    setIsAddOpen(false)
  }

  function addExercise(exercise: Exercise, values: ExerciseValues) {
    const draft: DraftExercise = {
      id: `new-${crypto.randomUUID()}`,
      workout: workoutId ?? '',
      exercise: {
        id: exercise.id,
        name: exercise.name,
        prescription_type: exercise.prescription_type,
        muscle_group: exercise.muscle_group,
      },
      exerciseName: exercise.name,
      prescription: '',
      sort_order: draftExercises.length,
      note: '',
      ...values,
      isNew: true,
    }
    setDraftExercises((current) => [...current, draft])
  }

  function updateExercise(next: WorkoutExerciseDisplay) {
    setDraftExercises((current) =>
      current.map((exercise) =>
        exercise.id === next.id ? { ...next, isNew: exercise.isNew } : exercise,
      ),
    )
  }

  function removeExercise(exercise: WorkoutExerciseDisplay) {
    setDraftExercises((current) => current.filter((item) => item.id !== exercise.id))
  }

  function reorder(activeId: string, overId: string) {
    if (activeId === overId) return

    setDraftExercises((current) => {
      const oldIndex = current.findIndex((exercise) => exercise.id === activeId)
      const newIndex = current.findIndex((exercise) => exercise.id === overId)
      return oldIndex === -1 || newIndex === -1
        ? current
        : arrayMove(current, oldIndex, newIndex)
    })
  }

  return {
    isEditing,
    draftExercises,
    draftWorkoutName,
    isAddOpen,
    exerciseLibrary: exerciseLibrary.data ?? [],
    muscleGroupFilter,
    isExerciseLibraryLoading: exerciseLibrary.isLoading,
    isCreatingExercise: createExerciseMutation.isPending,
    saveError: saveMutation.error,
    isSaving: saveMutation.isPending,
    startEditing,
    setDraftWorkoutName,
    cancelEditing,
    save: () => saveMutation.mutate(),
    openAddDialog: () => setIsAddOpen(true),
    setIsAddOpen,
    setMuscleGroupFilter,
    addExercise,
    createExercise: (input: ExerciseInput) => createExerciseMutation.mutateAsync(input),
    updateExercise,
    removeExercise,
    reorder,
  }
}

function toWorkoutExerciseInput(
  exercise: DraftExercise,
  sortOrder: number,
): WorkoutExerciseInput {
  return {
    exercise: typeof exercise.exercise === 'string' ? exercise.exercise : exercise.exercise.id,
    sets: exercise.sets,
    reps: exercise.reps,
    time: exercise.time,
    sort_order: sortOrder,
    weight: exercise.weight,
    weight_unit: exercise.weight_unit,
  }
}
