import { useParams } from 'react-router-dom'
import { getErrorMessage } from '../../../shared/api/errors'
import { InlineError } from '../../../shared/components/InlineError'
import { PrimaryButton } from '../../../shared/components/PrimaryButton'
import { ScrollableStack } from '../../../shared/layout/ScrollableStack'
import { TrainingLayout } from '../../../shared/layout/TrainingLayout'
import { RecommendationPanel } from '../../recommendations/components/RecommendationPanel'
import { useWorkoutRecommendation } from '../../recommendations/hooks/useWorkoutRecommendation'
import { ExerciseCard } from '../components/ExerciseCard'
import { useWorkoutPage } from '../hooks/useWorkoutPage'

export function WorkoutPage() {
  const { workoutId } = useParams()
  const { workout, exerciseDisplays, isLoading, error } = useWorkoutPage(workoutId)
  const recommendation = useWorkoutRecommendation(workoutId)

  return (
    <TrainingLayout>
      <section className="training-content workout-content">
        <div className="section-heading">
          <p className="eyebrow">Workout</p>
          <h1>{workout?.name ?? 'Workout'}</h1>
        </div>
        <div className="workout-status-stack">
          {isLoading ? <p className="muted">Loading workout...</p> : null}
          <InlineError message={error ? getErrorMessage(error) : null} />
        </div>
        <ScrollableStack
          empty={
            !isLoading ? (
              <p className="empty-state">This workout has no exercises yet.</p>
            ) : null
          }
        >
          {exerciseDisplays.map((exercise) => (
            <ExerciseCard key={exercise.id} exercise={exercise} />
          ))}
          {recommendation.recommendation ? (
            <RecommendationPanel
              recommendation={recommendation.recommendation}
              exerciseDisplays={exerciseDisplays}
              onAcceptOperation={recommendation.acceptOperation}
              onRejectOperation={recommendation.rejectOperation}
              acceptingOperationId={recommendation.acceptingOperationId}
              rejectingOperationId={recommendation.rejectingOperationId}
            />
          ) : null}
        </ScrollableStack>
        <div className="workout-status-stack">
          <InlineError
            message={
              recommendation.error ? getErrorMessage(recommendation.error) : null
            }
          />
        </div>
        {recommendation.isWorkoutReadyToSave ? (
          <PrimaryButton
            className="workout-recommendation-button"
            type="button"
            isLoading={recommendation.isSavingWorkout}
            onClick={recommendation.saveWorkout}
          >
            Save Workout
          </PrimaryButton>
        ) : !recommendation.recommendation ? (
          <PrimaryButton
            className="workout-recommendation-button"
            type="button"
            isLoading={recommendation.isGenerating}
            disabled={!workoutId}
            onClick={recommendation.generate}
          >
            Get Recommendation
          </PrimaryButton>
        ) : null}
      </section>
    </TrainingLayout>
  )
}
