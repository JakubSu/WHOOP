import { useState } from 'react'
import { ChevronDown, LoaderCircle } from 'lucide-react'
import { RecommendationOperationCard } from '../../recommendations/components/RecommendationOperationCard'
import { useRecommendation } from '../../recommendations/hooks/useWorkoutRecommendation'
import { type Recommendation } from '../../recommendations/types'
import { type CoachRecommendationReference } from '../types'

type Props = {
  recommendation: CoachRecommendationReference
}

export function CoachRecommendationCard({ recommendation }: Props) {
  if (!recommendation.actionable) {
    return <HistoricalRecommendationCard recommendation={recommendation} />
  }
  return <ActiveRecommendationCard recommendation={recommendation} />
}

function ActiveRecommendationCard({ recommendation }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [confirmAcceptAll, setConfirmAcceptAll] = useState(false)
  const detail = useRecommendation(recommendation.id, undefined, expanded)
  const snapshot = detail.recommendation?.coach_card_snapshot ?? recommendation.coach_card_snapshot
  const workoutGroups = snapshot?.workout_groups ?? []
  const run = async (action: () => Promise<unknown>) => { await action() }
  const pendingCount = workoutGroups.reduce((total, group) => total + group.summary.pending, 0)

  if (detail.recommendation && detail.recommendation.status !== 'active') {
    return <HistoricalRecommendationCard recommendation={{
      ...recommendation,
      status: detail.recommendation.status,
      actionable: false,
      coach_card_snapshot: detail.recommendation.coach_card_snapshot,
    }} />
  }

  return (
    <section className="mt-3 overflow-hidden rounded-lg border border-primary/30 bg-background" aria-label="Active coach recommendation">
      <div className="flex items-center justify-between gap-3 px-3 py-3">
        <button className="min-w-0 flex-1 text-left" type="button" onClick={() => setExpanded((value) => !value)} aria-expanded={expanded}>
          <strong className="block text-sm">Training recommendation</strong>
          <span className="text-xs text-muted-foreground">{pendingCount} pending change{pendingCount === 1 ? '' : 's'} across {workoutGroups.length} workout{workoutGroups.length === 1 ? '' : 's'}</span>
        </button>
        <ChevronDown className={expanded ? 'rotate-180 transition-transform' : 'transition-transform'} size={18} />
      </div>
      {expanded ? <div className="grid gap-3 border-t border-border p-3">
        <div className="flex flex-wrap gap-2">
          {confirmAcceptAll ? <>
            <button className="rounded bg-primary px-2 py-1 text-xs text-primary-foreground" type="button" disabled={detail.isBulkAccepting} onClick={() => void run(async () => { const result = await detail.acceptAll(); setConfirmAcceptAll(false); return result })}>Confirm accept all</button>
            <button className="rounded border px-2 py-1 text-xs" type="button" onClick={() => setConfirmAcceptAll(false)}>Cancel</button>
          </> : <>
            <button className="rounded bg-primary px-2 py-1 text-xs text-primary-foreground" type="button" onClick={() => setConfirmAcceptAll(true)}>Accept all</button>
            <button className="rounded border px-2 py-1 text-xs" type="button" disabled={detail.isBulkRejecting} onClick={() => void run(detail.rejectAll)}>Reject all</button>
          </>}
        </div>
        {workoutGroups.map((group) => <details key={group.id} className="rounded-md border bg-card p-3">
          <summary className="cursor-pointer text-sm font-medium">{group.title} <span className="font-normal text-muted-foreground">· {group.summary.pending} pending</span></summary>
          <ReadOnlyWorkout workout={detail.recommendation?.workouts.find((item) => item.id === group.id)} />
          <ActionableOperations operationIds={group.operation_ids} detail={detail} />
        </details>)}
        {detail.error ? <p className="text-xs text-destructive">Could not update this recommendation. Try again.</p> : null}
      </div> : null}
    </section>
  )
}

function ReadOnlyWorkout({ workout }: { workout: Recommendation['workouts'][number] | undefined }) {
  if (!workout) return null
  return <div className="mt-3 rounded border border-border/70 p-2 text-xs">
    <p className="font-medium">{workout.workout.name} · {workout.workout.date}</p>
    <ul className="mt-2 grid gap-1 text-muted-foreground">
      {workout.exercises.map((exercise) => <li key={exercise.id}>{exercise.exercise.name} · {exercise.sets} × {exercise.reps}</li>)}
    </ul>
  </div>
}

function HistoricalRecommendationCard({ recommendation }: Props) {
  const workoutGroups = recommendation.coach_card_snapshot?.workout_groups ?? []

  return <section className="mt-3 rounded-lg border border-border bg-muted/30 px-3 py-3" aria-label="Historical coach recommendation">
    <strong className="block text-sm">Training recommendation</strong>
    <p className="mt-1 text-xs text-muted-foreground">{statusLabel(recommendation.status)}</p>
    <div className="mt-2 grid gap-1 text-xs text-muted-foreground">
      {workoutGroups.map((group) => <div key={group.id}>{group.title} · {outcomeLabel(group.summary)}</div>)}
    </div>
  </section>
}

function ActionableOperations({ operationIds, detail }: {
  operationIds: string[]
  detail: ReturnType<typeof useRecommendation>
}) {
  if (detail.isLoading) return <p className="mt-3 flex items-center gap-2 text-xs text-muted-foreground"><LoaderCircle className="size-3 animate-spin" /> Loading workout…</p>
  const operations = detail.recommendation?.operations.filter((operation) => operationIds.includes(operation.id)) ?? []
  return <div className="mt-3 grid gap-2">{operations.map((operation) => <RecommendationOperationCard key={operation.id} operation={operation} exercise={undefined} exerciseLibrary={detail.exerciseLibrary} onSave={detail.saveOperation} onAccept={() => void detail.acceptOperation(operation.id)} onReject={() => void detail.rejectOperation(operation.id)} isSaving={detail.savingOperationId === operation.id} isAccepting={detail.acceptingOperationId === operation.id} isRejecting={detail.rejectingOperationId === operation.id} />)}</div>
}

function outcomeLabel(summary: { accepted: number; rejected: number; stale: number }) {
  return [`${summary.accepted} accepted`, `${summary.rejected} rejected`, summary.stale ? `${summary.stale} no longer available` : ''].filter(Boolean).join(' · ')
}

function statusLabel(status: CoachRecommendationReference['status']) {
  return status === 'superseded' ? 'Replaced by a newer recommendation' : status === 'completed' ? 'Resolved' : 'No longer available'
}
