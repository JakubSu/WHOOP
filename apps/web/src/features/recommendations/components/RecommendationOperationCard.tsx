import { Check, X } from 'lucide-react'
import { PrimaryButton } from '../../../shared/components/PrimaryButton'
import { type RecommendationOperation } from '../types'
import { type WorkoutExerciseDisplay } from '../../training/types'

type RecommendationOperationCardProps = {
  operation: RecommendationOperation
  exerciseDisplays: WorkoutExerciseDisplay[]
  fallbackReason: string
  onAccept: () => void
  onReject: () => void
  isAccepting: boolean
  isRejecting: boolean
}

type OperationBadge = 'Update' | 'Replace' | 'Add' | 'Remove'

type ChangeValue = string | number | boolean | null

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function stringValue(value: unknown) {
  return typeof value === 'string' ? value : null
}

function displayValue(value: unknown) {
  if (value === null || value === undefined || value === '') {
    return 'none'
  }

  return String(value)
}

function labelForField(field: string) {
  const labels: Record<string, string> = {
    sets: 'Sets',
    reps: 'Reps',
    time: 'Time',
    weight: 'Weight',
    weight_unit: 'Weight unit',
    note: 'Note',
    notes: 'Notes',
    duration_seconds: 'Duration',
    rest_seconds: 'Rest',
  }

  return labels[field] ?? field.replaceAll('_', ' ')
}

function badgeFor(operationType: RecommendationOperation['operation_type']): OperationBadge {
  if (operationType === 'replace_exercise') {
    return 'Replace'
  }
  if (operationType === 'add_exercise') {
    return 'Add'
  }
  if (operationType === 'remove_exercise') {
    return 'Remove'
  }
  return 'Update'
}

function changedValues(
  operation: RecommendationOperation,
  exercise: WorkoutExerciseDisplay | undefined,
) {
  if (!isRecord(operation.payload.changes)) {
    return []
  }

  return Object.entries(operation.payload.changes).map(([field, next]) => ({
    field,
    label: labelForField(field),
    previous: exercise?.[field as keyof WorkoutExerciseDisplay] as
      | ChangeValue
      | undefined,
    next,
  }))
}

function exerciseForOperation(
  operation: RecommendationOperation,
  exerciseDisplays: WorkoutExerciseDisplay[],
) {
  const workoutExerciseId = stringValue(operation.payload.workout_exercise_id)
  if (!workoutExerciseId) {
    return undefined
  }

  return exerciseDisplays.find((exercise) => exercise.id === workoutExerciseId)
}

function namesFromReplaceText(displayText: string) {
  const match = displayText.match(/^Replace (.+) with (.+)$/)
  if (!match) {
    return null
  }

  return { previous: match[1], next: match[2] }
}

function reasonFor(operation: RecommendationOperation, fallbackReason: string) {
  return stringValue(operation.payload.reason) ?? fallbackReason
}

function addExerciseTitle(operation: RecommendationOperation) {
  const exerciseName = stringValue(operation.payload.exercise_name)
  if (exerciseName) {
    return exerciseName
  }

  return operation.display_text
}

function proposedPrescription(operation: RecommendationOperation) {
  const parts = []
  const sets = operation.payload.sets
  const reps = operation.payload.reps
  const time = operation.payload.time ?? operation.payload.duration_seconds
  const weight = operation.payload.weight
  const weightUnit = stringValue(operation.payload.weight_unit) ?? 'lb'

  if (typeof sets === 'number' && typeof reps === 'number' && sets > 0 && reps > 0) {
    parts.push(`${sets} sets x ${reps} reps`)
  }
  if (typeof time === 'number' && time > 0) {
    parts.push(`${time} sec`)
  }
  if ((typeof weight === 'number' || typeof weight === 'string') && String(weight)) {
    parts.push(`${displayValue(weight)} ${weightUnit}`)
  }

  return parts.join(' / ')
}

function statusLabel(status: RecommendationOperation['status']) {
  return status[0].toUpperCase() + status.slice(1)
}

function OperationActions({
  operation,
  onAccept,
  onReject,
  isAccepting,
  isRejecting,
}: {
  operation: RecommendationOperation
  onAccept: () => void
  onReject: () => void
  isAccepting: boolean
  isRejecting: boolean
}) {
  const isPending = operation.status === 'pending'

  return (
    <div className="recommendation-actions">
      <PrimaryButton
        type="button"
        isLoading={isAccepting}
        disabled={!isPending || isRejecting}
        onClick={onAccept}
      >
        <Check aria-hidden="true" size={16} />
        Accept
      </PrimaryButton>
      <button
        className="reject-button"
        type="button"
        disabled={!isPending || isAccepting || isRejecting}
        onClick={onReject}
      >
        <X aria-hidden="true" size={16} />
        Reject
      </button>
    </div>
  )
}

export function RecommendationOperationCard({
  operation,
  exerciseDisplays,
  fallbackReason,
  onAccept,
  onReject,
  isAccepting,
  isRejecting,
}: RecommendationOperationCardProps) {
  const badge = badgeFor(operation.operation_type)
  const exercise = exerciseForOperation(operation, exerciseDisplays)
  const reason = reasonFor(operation, fallbackReason)

  if (operation.operation_type === 'update_exercise') {
    const changes = changedValues(operation, exercise)

    return (
      <article className="recommendation-card recommendation-card--neutral">
        <div className="recommendation-card__header">
          <div className="recommendation-card__badges">
            <span className="recommendation-badge">Update</span>
            <span className={`recommendation-status ${operation.status}`}>
              {statusLabel(operation.status)}
            </span>
          </div>
          <strong>{exercise?.exerciseName ?? operation.display_text}</strong>
        </div>
        {changes.length ? (
          <div className="recommendation-change-list">
            {changes.map((change) => (
              <div className="recommendation-change" key={change.field}>
                <span>{change.label}</span>
                <del>{displayValue(change.previous)}</del>
                <ins>{displayValue(change.next)}</ins>
              </div>
            ))}
          </div>
        ) : (
          <p className="recommendation-fallback">{operation.display_text}</p>
        )}
        {reason ? <p className="recommendation-reason">{reason}</p> : null}
        <OperationActions
          operation={operation}
          onAccept={onAccept}
          onReject={onReject}
          isAccepting={isAccepting}
          isRejecting={isRejecting}
        />
      </article>
    )
  }

  if (operation.operation_type === 'replace_exercise') {
    const names = namesFromReplaceText(operation.display_text)

    return (
      <article className="recommendation-card recommendation-card--neutral">
        <div className="recommendation-card__header">
          <div className="recommendation-card__badges">
            <span className="recommendation-badge">Replace</span>
            <span className={`recommendation-status ${operation.status}`}>
              {statusLabel(operation.status)}
            </span>
          </div>
          <strong>{exercise?.exerciseName ?? names?.previous ?? 'Exercise'}</strong>
        </div>
        <div className="recommendation-swap">
          <del>{exercise?.exerciseName ?? names?.previous ?? operation.display_text}</del>
          <ins>{names?.next ?? displayValue(operation.payload.replacement_exercise_id)}</ins>
        </div>
        {reason ? <p className="recommendation-reason">{reason}</p> : null}
        <OperationActions
          operation={operation}
          onAccept={onAccept}
          onReject={onReject}
          isAccepting={isAccepting}
          isRejecting={isRejecting}
        />
      </article>
    )
  }

  if (operation.operation_type === 'add_exercise') {
    const prescription = proposedPrescription(operation)
    const title = addExerciseTitle(operation)

    return (
      <article className="recommendation-card recommendation-card--positive">
        <div className="recommendation-card__header">
          <div className="recommendation-card__badges">
            <span className="recommendation-badge positive">Add</span>
            <span className={`recommendation-status ${operation.status}`}>
              {statusLabel(operation.status)}
            </span>
          </div>
          <strong>{title}</strong>
        </div>
        {prescription ? <ins>{prescription}</ins> : null}
        {reason ? <p className="recommendation-reason">{reason}</p> : null}
        <OperationActions
          operation={operation}
          onAccept={onAccept}
          onReject={onReject}
          isAccepting={isAccepting}
          isRejecting={isRejecting}
        />
      </article>
    )
  }

  return (
    <article className="recommendation-card recommendation-card--negative">
      <div className="recommendation-card__header">
        <div className="recommendation-card__badges">
          <span className="recommendation-badge negative">{badge}</span>
          <span className={`recommendation-status ${operation.status}`}>
            {statusLabel(operation.status)}
          </span>
        </div>
        <strong>{exercise?.exerciseName ?? operation.display_text}</strong>
      </div>
      <del>{exercise?.prescription ?? operation.display_text}</del>
      {reason ? <p className="recommendation-reason">{reason}</p> : null}
      <OperationActions
        operation={operation}
        onAccept={onAccept}
        onReject={onReject}
        isAccepting={isAccepting}
        isRejecting={isRejecting}
      />
    </article>
  )
}
