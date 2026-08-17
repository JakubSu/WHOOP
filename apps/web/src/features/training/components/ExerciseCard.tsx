import { Clock3, Dumbbell, GripVertical, Layers3, Repeat2, Trash2 } from 'lucide-react'
import { Card, Button } from '@/shared/components/ui'
import { type ButtonHTMLAttributes } from 'react'
import { Input } from '@/shared/components/ui'
import { type WorkoutExerciseDisplay } from '../types'

type ExerciseCardProps = {
  exercise: WorkoutExerciseDisplay
  editable?: boolean
  dragHandleProps?: ButtonHTMLAttributes<HTMLButtonElement>
  dragHandleRef?: (node: HTMLButtonElement | null) => void
  onChange?: (exercise: WorkoutExerciseDisplay) => void
  onDelete?: (exercise: WorkoutExerciseDisplay) => void
}

export function ExerciseCard({
  exercise,
  editable = false,
  dragHandleProps,
  dragHandleRef,
  onChange,
  onDelete,
}: ExerciseCardProps) {
  const isTimed = typeof exercise.exercise !== 'string' && exercise.exercise.prescription_type === 'timed'

  return (
    <Card className="group relative flex items-center gap-3 rounded-lg border-border bg-card p-4 transition-colors hover:border-muted-foreground/40">
      {editable ? (
        <Button
          aria-label={`Move ${exercise.exerciseName}`}
          className="size-8 shrink-0 cursor-grab text-muted-foreground/50 hover:text-muted-foreground active:cursor-grabbing"
          ref={dragHandleRef}
          size="icon"
          title="Move exercise"
          type="button"
          variant="ghost"
          {...dragHandleProps}
        >
          <GripVertical aria-hidden="true" size={20} />
        </Button>
      ) : null}
      <div className="min-w-0 flex-1">
        <strong className={`block truncate text-[15px] font-semibold tracking-tight text-foreground${editable ? ' pr-9' : ''}`}>
          {exercise.exerciseName}
        </strong>
        {editable ? (
          <ExerciseFields exercise={exercise} onChange={onChange} />
        ) : (
          <dl className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] text-muted-foreground">
            {isTimed ? <Metric icon={<Clock3 aria-hidden="true" />} label="Time" value={formatTime(exercise.time)} /> : <>
              <Metric icon={<Layers3 aria-hidden="true" />} label="Sets" value={displayNumber(exercise.sets)} />
              <Metric icon={<Repeat2 aria-hidden="true" />} label="Reps" value={displayNumber(exercise.reps)} />
            </>}
            <Metric icon={<Dumbbell aria-hidden="true" />} label="Weight" value={formatWeight(exercise)} />
          </dl>
        )}
      </div>
      {editable ? (
        <div className="absolute right-3 top-1/2 flex -translate-y-1/2 items-center">
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

function ExerciseFields({ exercise, onChange }: Pick<ExerciseCardProps, 'exercise' | 'onChange'>) {
  const isTimed = typeof exercise.exercise !== 'string' && exercise.exercise.prescription_type === 'timed'
  const update = (values: Partial<WorkoutExerciseDisplay>) => onChange?.({ ...exercise, ...values })

  return (
    <div className="mt-2 flex flex-nowrap items-center gap-2">
      {isTimed ? (
        <>
          <Field label="Seconds">
            <Input aria-label={`${exercise.exerciseName} seconds`} className="h-8 w-16 px-2 text-base sm:w-20 sm:text-[13px]" min="0" type="number" value={exercise.time} onChange={(event) => update({ time: numberValue(event.target.value) })} />
          </Field>
          <Field label={exercise.weight_unit || 'lb'}>
            <Input aria-label={`${exercise.exerciseName} weight`} className="h-8 w-14 px-1.5 text-base sm:w-20 sm:text-[13px]" min="0" step="1" type="number" value={wholeNumberWeight(exercise.weight ?? '') ?? ''} onChange={(event) => update({ weight: wholeNumberWeight(event.target.value) })} />
          </Field>
        </>
      ) : (
        <>
          <Field label="Sets"><Input aria-label={`${exercise.exerciseName} sets`} className="h-8 w-10 px-1.5 text-base sm:w-14 sm:text-[13px]" min="0" type="number" value={exercise.sets} onChange={(event) => update({ sets: numberValue(event.target.value) })} /></Field>
          <Field label="Reps"><Input aria-label={`${exercise.exerciseName} reps`} className="h-8 w-10 px-1.5 text-base sm:w-14 sm:text-[13px]" min="0" type="number" value={exercise.reps} onChange={(event) => update({ reps: numberValue(event.target.value) })} /></Field>
          <Field label={exercise.weight_unit || 'lb'}><Input aria-label={`${exercise.exerciseName} weight`} className="h-8 w-14 px-1.5 text-base sm:w-20 sm:text-[13px]" inputMode="numeric" min="0" step="1" type="number" value={wholeNumberWeight(exercise.weight ?? '') ?? ''} onChange={(event) => update({ weight: wholeNumberWeight(event.target.value) })} /></Field>
        </>
      )}
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex shrink-0 items-center gap-1">
      {children}
      <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/50">{label}</span>
    </div>
  )
}

function numberValue(value: string) {
  return value === '' ? 0 : Number(value)
}

function wholeNumberWeight(value: string) {
  return value === '' ? null : String(Math.trunc(Number(value)))
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

function formatTime(seconds: number) {
  return seconds > 0 ? `${seconds} sec` : '—'
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
