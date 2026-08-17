import { useEffect, useMemo, useState } from 'react'
import { X } from 'lucide-react'
import { getErrorMessage } from '@/shared/api/errors'
import { Alert, Button, Dialog, DialogContent, DialogTitle, Input, Label } from '@/shared/components/ui'
import { type ExerciseInput } from '../api/trainingApi'
import { type Exercise } from '../types'
import { MUSCLE_GROUP_LABELS, MUSCLE_GROUPS, type MuscleGroup } from '../constants/muscleGroups'

export type ExercisePickerIntent =
  | { kind: 'workout'; onSelect: (exercise: Exercise, values: ExerciseValues) => void }
  | { kind: 'coach'; onSelect: (exercise: Exercise) => void; onCreate: (exercise: Exercise) => void }

type AddExerciseDialogProps = {
  exercises: Exercise[]
  isLoading: boolean
  isCreating: boolean
  muscleGroupFilter: MuscleGroup | undefined
  open: boolean
  onOpenChange: (open: boolean) => void
  onMuscleGroupFilterChange: (muscleGroup: MuscleGroup | undefined) => void
  intent: ExercisePickerIntent
  onCreate: (input: ExerciseInput) => Promise<Exercise>
  initialDefinition?: Partial<ExerciseInput>
  initialStep?: 'search' | 'create'
  initialQuery?: string
  allowCreateFromSearch?: boolean
}

export type ExerciseValues = {
  sets: number
  reps: number
  time: number
  weight: string | null
  weight_unit: string
}

type DialogStep = 'search' | 'create' | 'prescription'

export function AddExerciseDialog({
  exercises,
  isLoading,
  isCreating,
  muscleGroupFilter,
  open,
  onOpenChange,
  onMuscleGroupFilterChange,
  intent,
  onCreate,
  initialDefinition,
  initialStep = 'search',
  initialQuery = '',
  allowCreateFromSearch = true,
}: AddExerciseDialogProps) {
  const [step, setStep] = useState<DialogStep>(initialStep)
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<Exercise | null>(null)
  const [values, setValues] = useState<ExerciseValues | null>(null)
  const [definition, setDefinition] = useState<ExerciseInput>(() => definitionFrom(initialDefinition))
  const [createError, setCreateError] = useState<string | null>(null)
  const normalizedQuery = query.trim().toLowerCase()
  const matchingExercises = useMemo(
    () => exercises.filter((exercise) => exercise.name.toLowerCase().includes(normalizedQuery)),
    [exercises, normalizedQuery],
  )
  const isTimed = selected?.prescription_type === 'timed'
  const isCreatingTimedExercise = definition.prescription_type === 'timed'

  useEffect(() => {
    if (!open) return
    setStep(initialStep)
    setQuery(initialStep === 'create' ? initialDefinition?.name ?? '' : initialQuery)
    setSelected(null)
    setValues(null)
    setDefinition(definitionFrom(initialDefinition))
    setCreateError(null)
  }, [initialStep, open])

  function close() {
    setStep('search')
    setQuery('')
    setSelected(null)
    setValues(null)
    setDefinition(definitionFrom(initialDefinition))
    setCreateError(null)
    onOpenChange(false)
  }

  function selectExercise(exercise: Exercise) {
    if (intent.kind === 'coach') {
      intent.onSelect(exercise)
      close()
      return
    }
    setSelected(exercise)
    setValues({
      sets: exercise.prescription_type === 'strength' ? exercise.default_sets : 0,
      reps: exercise.prescription_type === 'strength' ? exercise.default_reps : 0,
      time: exercise.prescription_type === 'timed' ? exercise.default_time : 0,
      weight: exercise.default_weight,
      weight_unit: exercise.default_weight_unit || 'lb',
    })
    setStep('prescription')
  }

  function openCreate() {
    setDefinition(definitionFrom({ ...initialDefinition, name: query.trim() }))
    setCreateError(null)
    setStep('create')
  }

  function setPrescriptionType(prescriptionType: Exercise['prescription_type']) {
    setDefinition((current) => prescriptionType === 'timed'
      ? { ...current, prescription_type: prescriptionType, default_sets: 0, default_reps: 0 }
      : { ...current, prescription_type: prescriptionType, default_time: 0 })
  }

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalizedName = definition.name.trim().toLowerCase()
    const existing = exercises.find((exercise) => exercise.name.trim().toLowerCase() === normalizedName)
    if (existing) {
      selectExercise(existing)
      return
    }

    try {
      const exercise = await onCreate({
        ...definition,
        name: definition.name.trim(),
        default_sets: isCreatingTimedExercise ? 0 : definition.default_sets,
        default_reps: isCreatingTimedExercise ? 0 : definition.default_reps,
        default_weight: definition.default_weight,
        default_time: isCreatingTimedExercise ? definition.default_time : 0,
      })
      if (intent.kind === 'coach') {
        intent.onCreate(exercise)
        close()
      } else {
        selectExercise(exercise)
      }
    } catch (error) {
      setCreateError(getErrorMessage(error))
    }
  }

  return (
    <Dialog open={open} onOpenChange={(nextOpen) => nextOpen ? onOpenChange(true) : close()}>
      <DialogContent aria-describedby={undefined}>
        <DialogTitle className="text-lg font-bold">{step === 'create' ? 'Create exercise' : intent.kind === 'coach' ? 'Choose exercise' : 'Add exercise'}</DialogTitle>

        {step === 'search' ? (
          <div className="mt-4">
            <Label htmlFor="exercise-search">Search exercise library</Label>
            <div className="relative mt-2">
              <Input className="pr-11" id="exercise-search" autoFocus placeholder="Search exercises" value={query} onChange={(event) => setQuery(event.target.value)} />
              {query ? <Button aria-label="Clear search" className="absolute right-0 top-0 text-muted-foreground" size="icon" type="button" variant="ghost" onClick={() => setQuery('')}><X aria-hidden="true" size={18} /></Button> : null}
            </div>
            <div className="mt-3"><Label htmlFor="exercise-muscle-group-filter">Muscle group</Label><select id="exercise-muscle-group-filter" className="mt-1 h-11 w-full rounded-md border border-input bg-background px-3 text-base sm:text-sm" value={muscleGroupFilter ?? ''} onChange={(event) => onMuscleGroupFilterChange(event.target.value === '' ? undefined : event.target.value as MuscleGroup)}><option value="">All muscle groups</option>{MUSCLE_GROUPS.map((muscleGroup) => <option key={muscleGroup} value={muscleGroup}>{MUSCLE_GROUP_LABELS[muscleGroup]}</option>)}</select></div>
            <div className="mt-3 max-h-72 space-y-1 overflow-y-auto">
              {isLoading ? <p className="p-2 text-sm text-muted-foreground">Loading exercises…</p> : null}
              {!isLoading && allowCreateFromSearch && normalizedQuery && matchingExercises.length === 0 ? (
                <div className="space-y-3 p-2 text-sm text-muted-foreground">
                  <p>No matching exercises.</p>
                  <Button className="w-full" type="button" onClick={openCreate}>Create “{query.trim()}”</Button>
                </div>
              ) : null}
              {matchingExercises.map((exercise) => <Button className="h-auto w-full justify-start px-3 py-3 text-left" key={exercise.id} type="button" variant="ghost" onClick={() => selectExercise(exercise)}><span>{exercise.name}</span><span className="ml-auto text-xs font-normal text-muted-foreground">{exercise.muscle_group}</span></Button>)}
            </div>
          </div>
        ) : null}

        {step === 'create' ? (
          <form className="mt-4 space-y-4" onSubmit={handleCreate}>
            {createError ? <Alert>{createError}</Alert> : null}
            <div><Label htmlFor="created-exercise-name">Exercise name</Label><Input id="created-exercise-name" className="mt-1" autoFocus required value={definition.name} onChange={(event) => setDefinition({ ...definition, name: event.target.value })} /></div>
            <div><Label htmlFor="created-exercise-type">Prescription type</Label><select id="created-exercise-type" className="mt-1 h-11 w-full rounded-md border border-input bg-background px-3 text-base sm:text-sm" value={definition.prescription_type} onChange={(event) => setPrescriptionType(event.target.value as Exercise['prescription_type'])}><option value="strength">Strength</option><option value="timed">Timed</option></select></div>
            <div><Label htmlFor="created-exercise-muscle-group">Muscle group</Label><select id="created-exercise-muscle-group" className="mt-1 h-11 w-full rounded-md border border-input bg-background px-3 text-base sm:text-sm" required value={definition.muscle_group} onChange={(event) => setDefinition({ ...definition, muscle_group: event.target.value as MuscleGroup })}>{MUSCLE_GROUPS.map((muscleGroup) => <option key={muscleGroup} value={muscleGroup}>{MUSCLE_GROUP_LABELS[muscleGroup]}</option>)}</select></div>
            {isCreatingTimedExercise ? <div className="grid grid-cols-2 gap-3"><NumberField label="Default seconds" value={definition.default_time} onChange={(default_time) => setDefinition({ ...definition, default_time })} /><div><Label htmlFor="created-exercise-weight">Default weight</Label><Input id="created-exercise-weight" className="mt-1" min="0" step="0.01" type="number" value={definition.default_weight ?? ''} onChange={(event) => setDefinition({ ...definition, default_weight: event.target.value || null })} /></div><UnitField id="created-exercise-unit" value={definition.default_weight_unit} onChange={(default_weight_unit) => setDefinition({ ...definition, default_weight_unit })} /></div> : <div className="grid grid-cols-2 gap-3"><NumberField label="Default sets" value={definition.default_sets} onChange={(default_sets) => setDefinition({ ...definition, default_sets })} /><NumberField label="Default reps" value={definition.default_reps} onChange={(default_reps) => setDefinition({ ...definition, default_reps })} /><div><Label htmlFor="created-exercise-weight">Default weight</Label><Input id="created-exercise-weight" className="mt-1" min="0" step="0.01" type="number" value={definition.default_weight ?? ''} onChange={(event) => setDefinition({ ...definition, default_weight: event.target.value || null })} /></div><UnitField id="created-exercise-unit" value={definition.default_weight_unit} onChange={(default_weight_unit) => setDefinition({ ...definition, default_weight_unit })} /></div>}
            <div className="flex justify-end gap-2 pt-2"><Button type="button" variant="outline" disabled={isCreating} onClick={() => setStep('search')}>Back</Button><Button type="submit" disabled={isCreating}>{isCreating ? 'Creating…' : 'Create exercise'}</Button></div>
          </form>
        ) : null}

        {step === 'prescription' && selected && values ? (
          <form className="mt-4 space-y-3" onSubmit={(event) => { event.preventDefault(); intent.kind === 'workout' && intent.onSelect(selected, values); close() }}>
            <div className="flex items-center justify-between"><p className="font-semibold">{selected.name}</p><Button size="sm" type="button" variant="ghost" onClick={() => { setSelected(null); setValues(null); setStep('search') }}>Change</Button></div>
            {isTimed ? <div className="grid grid-cols-2 gap-3"><NumberField label="Seconds" value={values.time} onChange={(time) => setValues({ ...values, time })} /><div><Label htmlFor="new-exercise-weight">Weight</Label><Input id="new-exercise-weight" className="mt-1" min="0" step="0.01" type="number" value={values.weight ?? ''} onChange={(event) => setValues({ ...values, weight: event.target.value || null })} /></div><UnitField id="new-exercise-unit" value={values.weight_unit} onChange={(weight_unit) => setValues({ ...values, weight_unit })} /></div> : <div className="grid grid-cols-2 gap-3"><NumberField label="Sets" value={values.sets} onChange={(sets) => setValues({ ...values, sets })} /><NumberField label="Reps" value={values.reps} onChange={(reps) => setValues({ ...values, reps })} /><div><Label htmlFor="new-exercise-weight">Weight</Label><Input id="new-exercise-weight" className="mt-1" min="0" step="0.01" type="number" value={values.weight ?? ''} onChange={(event) => setValues({ ...values, weight: event.target.value || null })} /></div><UnitField id="new-exercise-unit" value={values.weight_unit} onChange={(weight_unit) => setValues({ ...values, weight_unit })} /></div>}
            <div className="flex justify-end gap-2 pt-2"><Button type="button" variant="outline" onClick={close}>Cancel</Button><Button type="submit">Add exercise</Button></div>
          </form>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

function definitionFrom(initialDefinition?: Partial<ExerciseInput>): ExerciseInput {
  return {
    name: '',
    prescription_type: 'strength',
    default_sets: 0,
    default_reps: 0,
    default_weight: null,
    default_weight_unit: 'lb',
    muscle_group: 'other',
    default_time: 0,
    notes: '',
    ...initialDefinition,
  }
}

function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  const id = `new-exercise-${label.toLowerCase().replaceAll(' ', '-')}`
  return <div><Label htmlFor={id}>{label}</Label><Input id={id} className="mt-1" min="0" type="number" value={value} onChange={(event) => onChange(event.target.value === '' ? 0 : Number(event.target.value))} /></div>
}

function UnitField({ id, value, onChange }: { id: string; value: string; onChange: (value: string) => void }) {
  return <div><Label htmlFor={id}>Unit</Label><select id={id} className="mt-1 h-11 w-full rounded-md border border-input bg-background px-3 text-base sm:text-sm" value={value} onChange={(event) => onChange(event.target.value)}><option value="lb">lb</option><option value="kg">kg</option></select></div>
}
