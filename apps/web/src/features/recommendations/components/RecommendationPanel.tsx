import { RecommendationOperationCard } from './RecommendationOperationCard'
import { type Recommendation } from '../types'
import { type WorkoutExerciseDisplay } from '../../training/types'

type RecommendationPanelProps = {
  recommendation: Recommendation
  exerciseDisplays: WorkoutExerciseDisplay[]
  onAcceptOperation: (operationId: string) => void
  onRejectOperation: (operationId: string) => void
  acceptingOperationId: string | null
  rejectingOperationId: string | null
}

export function RecommendationPanel({
  recommendation,
  exerciseDisplays,
  onAcceptOperation,
  onRejectOperation,
  acceptingOperationId,
  rejectingOperationId,
}: RecommendationPanelProps) {
  return (
    <section className="recommendation-panel">
      {recommendation.summary ? (
        <p className="recommendation-panel__summary">{recommendation.summary}</p>
      ) : null}
      {recommendation.operations.map((operation) => (
        <RecommendationOperationCard
          key={operation.id}
          operation={operation}
          exerciseDisplays={exerciseDisplays}
          fallbackReason={recommendation.reason || recommendation.summary}
          onAccept={() => onAcceptOperation(operation.id)}
          onReject={() => onRejectOperation(operation.id)}
          isAccepting={acceptingOperationId === operation.id}
          isRejecting={rejectingOperationId === operation.id}
        />
      ))}
    </section>
  )
}
