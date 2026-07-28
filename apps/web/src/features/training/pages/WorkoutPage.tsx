import { ArrowLeft } from 'lucide-react'
import { useMemo } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { getErrorMessage } from '../../../shared/api/errors'
import { InlineError } from '../../../shared/components/InlineError'
import { PrimaryButton } from '../../../shared/components/PrimaryButton'
import { ScrollableStack } from '../../../shared/layout/ScrollableStack'
import { TrainingLayout } from '../../../shared/layout/TrainingLayout'
import { useCoachPageContext } from '../../coach/context/CoachOverlayContext'
import { getCoachPageContextForRoute } from '../../coach/services/coachContext'
import { RecommendationPanel } from '../../recommendations/components/RecommendationPanel'
import { useWorkoutRecommendation } from '../../recommendations/hooks/useWorkoutRecommendation'
import { ExerciseCard } from '../components/ExerciseCard'
import { useWorkoutPage } from '../hooks/useWorkoutPage'
import {
  getWorkoutScreenEyebrow,
  getWorkoutScreenTitle,
} from '../services/formatters'

export function WorkoutPage() {
  const { workoutId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const {
    resolvedWorkoutId,
    workout,
    exerciseDisplays,
    isToday,
    landingMessage,
    isLoading,
    error,
  } =
    useWorkoutPage(workoutId)
  const recommendation = useWorkoutRecommendation(resolvedWorkoutId)
  const primaryTitle = getWorkoutScreenTitle(workout?.date ?? null, isToday)
  const eyebrow = getWorkoutScreenEyebrow(landingMessage)
  const coachContext = useMemo(
    () => getCoachPageContextForRoute(location.pathname),
    [location.pathname],
  )
  useCoachPageContext(coachContext)

  return (
    <TrainingLayout>
      <section className="training-content workout-content">
        <div className="section-heading">
          <div className="section-heading__actions">
            <p className="eyebrow">{eyebrow}</p>
            <PrimaryButton
              className="secondary-action back-to-plan-button"
              type="button"
              onClick={() => navigate('/plan')}
            >
              <ArrowLeft aria-hidden="true" size={17} />
              My Plan
            </PrimaryButton>
          </div>
          <h1>{workout ? primaryTitle : 'Workout'}</h1>
          {workout ? <p className="muted">{workout.name}</p> : null}
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
            disabled={!resolvedWorkoutId}
            onClick={recommendation.generate}
          >
            Get Recommendation
          </PrimaryButton>
        ) : null}
      </section>
    </TrainingLayout>
  )
}
