import { useMemo } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { getErrorMessage } from '../../../shared/api/errors'
import { InlineError } from '../../../shared/components/InlineError'
import { ScrollableStack } from '../../../shared/layout/ScrollableStack'
import { TrainingLayout } from '../../../shared/layout/TrainingLayout'
import { useCoachPageContext } from '../../coach/context/CoachOverlayContext'
import { getCoachPageContextForRoute } from '../../coach/services/coachContext'
import { AddExerciseDialog } from '../components/AddExerciseDialog'
import { WorkoutExerciseList } from '../components/WorkoutExerciseList'
import { WorkoutHeader } from '../components/WorkoutHeader'
import { useWorkoutEditor } from '../hooks/useWorkoutEditor'
import { useWorkoutPage } from '../hooks/useWorkoutPage'

export function WorkoutPage() {
  const { workoutId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const workoutPage = useWorkoutPage(workoutId)
  const editor = useWorkoutEditor(
    workoutPage.resolvedWorkoutId,
    workoutPage.exerciseDisplays,
    workoutPage.workout?.name,
  )
  const coachContext = useMemo(
    () => getCoachPageContextForRoute(location.pathname),
    [location.pathname],
  )
  useCoachPageContext(coachContext)
  const visibleExercises = editor.isEditing
    ? editor.draftExercises
    : workoutPage.exerciseDisplays

  return (
    <TrainingLayout>
      <section className="mx-auto w-full max-w-2xl px-4 py-6 sm:px-6">
        <WorkoutHeader
          canEdit={Boolean(workoutPage.resolvedWorkoutId)}
          draftWorkoutName={editor.draftWorkoutName}
          exerciseCount={visibleExercises.length}
          isEditing={editor.isEditing}
          isLoading={workoutPage.isLoading}
          isSaving={editor.isSaving}
          isToday={workoutPage.isToday}
          nextWorkout={workoutPage.nextWorkout}
          previousWorkout={workoutPage.previousWorkout}
          workout={workoutPage.workout}
          onCancelEditing={editor.cancelEditing}
          onNext={() => workoutPage.nextWorkout && navigate(`/workouts/${workoutPage.nextWorkout.id}`)}
          onOpenWeek={() => workoutPage.workout?.date && navigate(`/week?date=${workoutPage.workout.date}`)}
          onPrevious={() => workoutPage.previousWorkout && navigate(`/workouts/${workoutPage.previousWorkout.id}`)}
          onSave={editor.save}
          onStartEditing={editor.startEditing}
          onWorkoutNameChange={editor.setDraftWorkoutName}
        />

        <div className="workout-status-stack">
          {workoutPage.isLoading ? <p className="muted">Loading workout...</p> : null}
          <InlineError message={workoutPage.error ? getErrorMessage(workoutPage.error) : null} />
          <InlineError message={editor.saveError ? getErrorMessage(editor.saveError) : null} />
        </div>

        <ScrollableStack empty={!workoutPage.isLoading && !editor.isEditing ? <p className="empty-state">This workout has no exercises yet.</p> : null}>
          <WorkoutExerciseList
            draftExercises={editor.draftExercises}
            exercises={workoutPage.exerciseDisplays}
            isEditing={editor.isEditing}
            onOpenAddDialog={editor.openAddDialog}
            onRemoveExercise={editor.removeExercise}
            onReorder={editor.reorder}
            onUpdateExercise={editor.updateExercise}
          />
        </ScrollableStack>

        <AddExerciseDialog
          exercises={editor.exerciseLibrary}
          isLoading={editor.isExerciseLibraryLoading}
          isCreating={editor.isCreatingExercise}
          muscleGroupFilter={editor.muscleGroupFilter}
          open={editor.isAddOpen}
          intent={{ kind: 'workout', onSelect: editor.addExercise }}
          onCreate={editor.createExercise}
          onOpenChange={editor.setIsAddOpen}
          onMuscleGroupFilterChange={editor.setMuscleGroupFilter}
        />
      </section>
    </TrainingLayout>
  )
}
