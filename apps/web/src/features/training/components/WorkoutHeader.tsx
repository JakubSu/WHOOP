import { ChevronLeft, ChevronRight, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Button, Dialog, DialogContent, DialogTitle, Input } from '@/shared/components/ui'
import { formatWeekdayDate } from '../services/formatters'
import { type Workout } from '../types'

type WorkoutHeaderProps = {
  workout: Workout | null | undefined
  previousWorkout: Workout | null | undefined
  nextWorkout: Workout | null | undefined
  isToday: boolean
  exerciseCount: number
  isLoading: boolean
  isEditing: boolean
  isSaving: boolean
  isDeleting: boolean
  canEdit: boolean
  canDelete: boolean
  draftWorkoutName: string
  onPrevious: () => void
  onNext: () => void
  onStartEditing: () => void
  onCancelEditing: () => void
  onSave: () => void
  onWorkoutNameChange: (name: string) => void
  onDelete: () => Promise<void>
}

export function WorkoutHeader({
  workout,
  previousWorkout,
  nextWorkout,
  isToday,
  exerciseCount,
  isLoading,
  isEditing,
  isSaving,
  isDeleting,
  canEdit,
  canDelete,
  draftWorkoutName,
  onPrevious,
  onNext,
  onStartEditing,
  onCancelEditing,
  onSave,
  onWorkoutNameChange,
  onDelete,
}: WorkoutHeaderProps) {
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const workoutDate = isToday ? 'Today' : formatWeekdayDate(workout?.date ?? null)

  return (
    <header className="mb-6 border-b border-border pb-5" data-tour="workout-header" data-tour-workout-date={workout?.date}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-primary">Workout</p>
        {isEditing ? (
          <div className="flex gap-2">
            <Button size="sm" type="button" variant="outline" disabled={isSaving} onClick={onCancelEditing}>Cancel</Button>
            <Button size="sm" type="button" disabled={isSaving} onClick={onSave}>{isSaving ? 'Saving…' : 'Save'}</Button>
          </div>
        ) : (
          <div className="flex gap-2">
            <Button size="sm" type="button" variant="outline" disabled={!canEdit} onClick={onStartEditing} data-tour="workout-edit">
              <Pencil aria-hidden="true" size={15} />Edit
            </Button>
            <Button className="border-destructive text-destructive hover:bg-destructive/10 hover:text-destructive" size="sm" type="button" variant="outline" disabled={!canDelete || isDeleting} onClick={() => setIsDeleteDialogOpen(true)}>
              <Trash2 aria-hidden="true" size={15} />Delete
            </Button>
          </div>
        )}
      </div>
      <div className="mt-2 grid grid-cols-[2.5rem_minmax(0,1fr)_2.5rem] items-center gap-2">
        <Button aria-label="Previous workout" type="button" variant="ghost" size="icon" disabled={!previousWorkout} onClick={onPrevious}><ChevronLeft aria-hidden="true" size={20} /></Button>
        {isEditing ? (
          <div className="min-w-0 px-2 py-1 text-center">
            <Input
              aria-label="Workout name"
              className="h-10 rounded-md border-border/70 bg-muted/40 px-3 text-center text-xl font-bold tracking-tight text-foreground shadow-sm transition-colors placeholder:text-muted-foreground/60 hover:border-muted-foreground/60 focus-visible:border-primary focus-visible:bg-background focus-visible:ring-2 focus-visible:ring-primary/20 sm:text-2xl"
              value={draftWorkoutName}
              onChange={(event) => onWorkoutNameChange(event.target.value)}
            />
            {workout ? <p className="mt-1 truncate text-sm text-muted-foreground">{workoutDate}</p> : null}
            {!isLoading ? <p className="mt-1 text-xs font-medium uppercase tracking-[0.12em] text-primary">{exerciseCount} {exerciseCount === 1 ? 'exercise' : 'exercises'}</p> : null}
          </div>
        ) : (
          <div className="min-w-0 px-2 py-1 text-center">
            <h1 className="truncate text-xl font-bold tracking-tight text-foreground sm:text-2xl">{workout?.name ?? 'Workout'}</h1>
            {workout ? <p className="mt-1 truncate text-sm text-muted-foreground">{workoutDate}</p> : null}
            {!isLoading ? <p className="mt-1 text-xs font-medium uppercase tracking-[0.12em] text-primary">{exerciseCount} {exerciseCount === 1 ? 'exercise' : 'exercises'}</p> : null}
          </div>
        )}
        <Button aria-label="Next workout" type="button" variant="ghost" size="icon" disabled={!nextWorkout} onClick={onNext}><ChevronRight aria-hidden="true" size={20} /></Button>
      </div>
      <Dialog open={isDeleteDialogOpen} onOpenChange={(open) => !isDeleting && setIsDeleteDialogOpen(open)}>
        <DialogContent aria-describedby={undefined}>
          <DialogTitle className="text-lg font-bold">Delete this workout?</DialogTitle>
          <p className="mt-2 text-sm text-muted-foreground">
            “{workout?.name ?? 'Workout'}” and all of its exercises will be permanently deleted.
          </p>
          <div className="mt-6 flex justify-end gap-2">
            <Button type="button" variant="outline" disabled={isDeleting} onClick={() => setIsDeleteDialogOpen(false)}>Cancel</Button>
            <Button type="button" variant="destructive" disabled={isDeleting} onClick={async () => { try { await onDelete() } finally { setIsDeleteDialogOpen(false) } }}>
              {isDeleting ? 'Deleting…' : 'Delete workout'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </header>
  )
}
