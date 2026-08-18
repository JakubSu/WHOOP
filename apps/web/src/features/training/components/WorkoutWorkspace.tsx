import { useMemo } from 'react'
import { CalendarDays, ChevronRight } from 'lucide-react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { getErrorMessage } from '../../../shared/api/errors'
import { InlineError } from '../../../shared/components/InlineError'
import { ScrollableStack } from '../../../shared/layout/ScrollableStack'
import { useCoachPageContext } from '../../coach/context/CoachOverlayContext'
import { getCoachPageContextForRoute } from '../../coach/services/coachContext'
import { Button } from '../../../shared/components/ui'
import { formatWeekRange } from '../services/formatters'
import { AddExerciseDialog } from './AddExerciseDialog'
import { WorkoutExerciseList } from './WorkoutExerciseList'
import { WorkoutHeader } from './WorkoutHeader'
import { useWorkoutEditor } from '../hooks/useWorkoutEditor'
import { useWorkoutPage } from '../hooks/useWorkoutPage'

export function WorkoutWorkspace() {
  const { workoutId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const workoutPage = useWorkoutPage(workoutId)
  const editor = useWorkoutEditor(workoutPage.resolvedWorkoutId, workoutPage.exerciseDisplays, workoutPage.workout?.name)
  const coachContext = useMemo(() => getCoachPageContextForRoute(location.pathname), [location.pathname])
  useCoachPageContext(coachContext)
  const visibleExercises = editor.isEditing ? editor.draftExercises : workoutPage.exerciseDisplays

  return <section className="mx-auto grid min-h-0 w-full max-w-2xl grid-rows-[auto_1fr] px-4 py-6 sm:px-6 lg:max-w-none lg:px-8 lg:py-7" data-tour-workspace-ready={!workoutPage.isLoading ? 'true' : undefined}>
    <Button
      className="mb-4 flex w-full justify-between border-border/70 px-3 text-sm font-semibold lg:hidden"
      aria-label={workoutPage.workout?.date ? `Open week of ${formatWeekRange(workoutPage.workout.date)}` : 'Open workout week'}
      type="button"
      variant="outline"
      disabled={editor.isEditing || !workoutPage.workout?.date}
      onClick={() => workoutPage.workout?.date && navigate(`/week?date=${workoutPage.workout.date}`)}
      data-tour="week-navigation-mobile"
    >
      <span className="flex min-w-0 items-center gap-2">
        <CalendarDays aria-hidden="true" size={16} className="shrink-0 text-primary" />
        <span className="truncate">{workoutPage.workout?.date ? `Week of ${formatWeekRange(workoutPage.workout.date)}` : 'View week'}</span>
      </span>
      <ChevronRight aria-hidden="true" size={17} className="shrink-0 text-muted-foreground" />
    </Button>
    <div className="grid min-h-0 grid-rows-[auto_auto_1fr]" data-tour="workout-panel">
      <WorkoutHeader canEdit={Boolean(workoutPage.resolvedWorkoutId)} draftWorkoutName={editor.draftWorkoutName} exerciseCount={visibleExercises.length} isEditing={editor.isEditing} isLoading={workoutPage.isLoading} isSaving={editor.isSaving} isToday={workoutPage.isToday} nextWorkout={workoutPage.nextWorkout} previousWorkout={workoutPage.previousWorkout} workout={workoutPage.workout} onCancelEditing={editor.cancelEditing} onNext={() => workoutPage.nextWorkout && navigate(`/workouts/${workoutPage.nextWorkout.id}`)} onPrevious={() => workoutPage.previousWorkout && navigate(`/workouts/${workoutPage.previousWorkout.id}`)} onSave={editor.save} onStartEditing={editor.startEditing} onWorkoutNameChange={editor.setDraftWorkoutName} />
      <div className="grid gap-2">
      {workoutPage.isLoading ? <p className="text-sm text-muted-foreground">Loading workout...</p> : null}
      <InlineError message={workoutPage.error ? getErrorMessage(workoutPage.error) : null} />
      <InlineError message={editor.saveError ? getErrorMessage(editor.saveError) : null} />
      </div>
      <ScrollableStack empty={!workoutPage.isLoading && !editor.isEditing ? <p className="grid place-items-center rounded-lg border border-dashed border-border px-3 py-8 text-center text-sm text-muted-foreground">This workout has no exercises yet.</p> : null}>
        <WorkoutExerciseList draftExercises={editor.draftExercises} exercises={workoutPage.exerciseDisplays} isEditing={editor.isEditing} onOpenAddDialog={editor.openAddDialog} onRemoveExercise={editor.removeExercise} onReorder={editor.reorder} onUpdateExercise={editor.updateExercise} />
      </ScrollableStack>
    </div>
    <AddExerciseDialog exercises={editor.exerciseLibrary} isLoading={editor.isExerciseLibraryLoading} isCreating={editor.isCreatingExercise} muscleGroupFilter={editor.muscleGroupFilter} open={editor.isAddOpen} intent={{ kind: 'workout', onSelect: editor.addExercise }} onCreate={editor.createExercise} onOpenChange={editor.setIsAddOpen} onMuscleGroupFilterChange={editor.setMuscleGroupFilter} />
  </section>
}
