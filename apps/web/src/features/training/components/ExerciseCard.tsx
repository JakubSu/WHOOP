import { Dumbbell, GripVertical, Layers3, Pencil, Repeat2, Trash2 } from 'lucide-react'
import { Card, Button } from '@/shared/components/ui'
import { type WorkoutExerciseDisplay } from '../types'

type ExerciseCardProps = {
  exercise: WorkoutExerciseDisplay
  editable?: boolean
  onEdit?: (exercise: WorkoutExerciseDisplay) => void
  onDelete?: (exercise: WorkoutExerciseDisplay) => void
}

export function ExerciseCard({
  exercise,
  editable = false,
  onEdit,
  onDelete,
}: ExerciseCardProps) {
  return (
    <Card className="group flex items-center gap-3 rounded-lg border-border bg-card p-4 transition-colors hover:border-muted-foreground/40">
      {editable ? (
        <Button
          aria-label={`Move ${exercise.exerciseName}`}
          className="size-8 shrink-0 cursor-grab text-muted-foreground/50 hover:text-muted-foreground active:cursor-grabbing"
          size="icon"
          title="Move exercise"
          type="button"
          variant="ghost"
        >
          <GripVertical aria-hidden="true" size={20} />
        </Button>
      ) : null}
      <div className="min-w-0 flex-1">
        <strong className="block truncate text-[15px] font-semibold tracking-tight text-foreground">
          {exercise.exerciseName}
        </strong>
        <dl className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] text-muted-foreground">
          <Metric icon={<Layers3 aria-hidden="true" />} label="Sets" value={displayNumber(exercise.sets)} />
          <Metric icon={<Repeat2 aria-hidden="true" />} label="Reps" value={displayNumber(exercise.reps)} />
          <Metric icon={<Dumbbell aria-hidden="true" />} label="Weight" value={formatWeight(exercise)} />
        </dl>
      </div>
      {editable ? (
        <div className="flex shrink-0 items-center gap-1 opacity-100 transition-opacity sm:opacity-0 sm:group-hover:opacity-100 sm:group-focus-within:opacity-100">
          <Button
            aria-label={`Edit ${exercise.exerciseName}`}
            className="size-8 text-muted-foreground hover:text-foreground"
            onClick={() => onEdit?.(exercise)}
            size="icon"
            title="Edit exercise"
            type="button"
            variant="ghost"
          >
            <Pencil aria-hidden="true" size={16} />
          </Button>
          <Button
            aria-label={`Delete ${exercise.exerciseName}`}
            className="size-8 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            onClick={() => onDelete?.(exercise)}
            size="icon"
            title="Delete exercise"
            type="button"
            variant="ghost"
          >
            <Trash2 aria-hidden="true" size={16} />
          </Button>
        </div>
      ) : null}
    </Card>
  )
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <dt className="text-muted-foreground/60 [&>svg]:size-3.5">{icon}</dt>
      <dd><span>{value}</span> <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/50">{label}</span></dd>
    </div>
  )
}

function displayNumber(value: number) {
  return value > 0 ? String(value) : '—'
}

function formatWeight(exercise: WorkoutExerciseDisplay) {
  if (!exercise.weight) {
    return '—'
  }

  const amount = Number(exercise.weight)
  const displayAmount = Number.isFinite(amount)
    ? amount.toLocaleString(undefined, { maximumFractionDigits: 2 })
    : exercise.weight
  return `${displayAmount} ${exercise.weight_unit || 'lb'}`
}
