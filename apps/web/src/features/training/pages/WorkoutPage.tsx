import { ChevronLeft, ChevronRight } from 'lucide-react'
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
import { getWorkoutScreenTitle } from '../services/formatters'

export function WorkoutPage() {
  const { workoutId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const {
    resolvedWorkoutId,
    workout,
    previousWorkout,
    nextWorkout,
    exerciseDisplays,
    isToday,
    isLoading,
    error,
  } =
    useWorkoutPage(workoutId)
  const recommendation = useWorkoutRecommendation(resolvedWorkoutId)
  const primaryTitle = getWorkoutScreenTitle(workout?.date ?? null, isToday)
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
            <p className="eyebrow">Workout</p>
            <PrimaryButton
              className="secondary-action back-to-week-button"
              type="button"
              disabled={!workout?.date}
              onClick={() => {
                if (workout?.date) {
                  navigate(`/week?date=${workout.date}`)
                }
              }}
            >
              Week
            </PrimaryButton>
          </div>
          <div className="workout-title-nav">
            <button
              className="workout-nav-button"
              type="button"
              aria-label="Previous workout"
              disabled={!previousWorkout}
              onClick={() => {
                if (previousWorkout) {
                  navigate(`/workouts/${previousWorkout.id}`)
                }
              }}
            >
              <ChevronLeft aria-hidden="true" size={21} />
            </button>
            <div className="workout-title-nav__title">
              <h1>{workout ? primaryTitle : 'Workout'}</h1>
              {workout ? <p className="muted">{workout.name}</p> : null}
            </div>
            <button
              className="workout-nav-button"
              type="button"
              aria-label="Next workout"
              disabled={!nextWorkout}
              onClick={() => {
                if (nextWorkout) {
                  navigate(`/workouts/${nextWorkout.id}`)
                }
              }}
            >
              <ChevronRight aria-hidden="true" size={21} />
            </button>
          </div>
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
