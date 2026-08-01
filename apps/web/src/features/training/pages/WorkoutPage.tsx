import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useMemo } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { getErrorMessage } from '../../../shared/api/errors'
import { InlineError } from '../../../shared/components/InlineError'
import { PrimaryButton } from '../../../shared/components/PrimaryButton'
import { Button } from '../../../shared/components/ui'
import { ScrollableStack } from '../../../shared/layout/ScrollableStack'
import { TrainingLayout } from '../../../shared/layout/TrainingLayout'
import { useCoachPageContext } from '../../coach/context/CoachOverlayContext'
import { getCoachPageContextForRoute } from '../../coach/services/coachContext'
import { RecommendationPanel } from '../../recommendations/components/RecommendationPanel'
import { useWorkoutRecommendation } from '../../recommendations/hooks/useWorkoutRecommendation'
import { ExerciseCard } from '../components/ExerciseCard'
import { useWorkoutPage } from '../hooks/useWorkoutPage'
import { formatWeekdayDate } from '../services/formatters'

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
  const workoutDate = isToday ? 'Today' : formatWeekdayDate(workout?.date ?? null)
  const coachContext = useMemo(
    () => getCoachPageContextForRoute(location.pathname),
    [location.pathname],
  )
  useCoachPageContext(coachContext)

  return (
    <TrainingLayout>
      <section className="mx-auto w-full max-w-2xl px-4 py-6 sm:px-6">
        <header className="mb-6 border-b border-border pb-5">
          <p className="text-center text-xs font-bold uppercase tracking-[0.16em] text-primary">Workout</p>
          <div className="mt-2 grid grid-cols-[2.5rem_minmax(0,1fr)_2.5rem] items-center gap-2">
            <Button
              aria-label="Previous workout"
              type="button"
              variant="ghost"
              size="icon"
              disabled={!previousWorkout}
              onClick={() => {
                if (previousWorkout) {
                  navigate(`/workouts/${previousWorkout.id}`)
                }
              }}
            >
              <ChevronLeft aria-hidden="true" size={20} />
            </Button>
            <button
              className="min-w-0 rounded-md px-2 py-1 text-center outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring"
              type="button"
              disabled={!workout?.date}
              onClick={() => {
                if (workout?.date) {
                  navigate(`/week?date=${workout.date}`)
                }
              }}
            >
              <h1 className="truncate text-xl font-bold tracking-tight text-foreground sm:text-2xl">
                {workout?.name ?? 'Workout'}
              </h1>
              {workout ? (
                <p className="mt-1 truncate text-sm text-muted-foreground">{workoutDate}</p>
              ) : null}
              {!isLoading ? (
                <p className="mt-1 text-xs font-medium uppercase tracking-[0.12em] text-primary">
                  {exerciseDisplays.length} {exerciseDisplays.length === 1 ? 'exercise' : 'exercises'}
                </p>
              ) : null}
              <span className="sr-only">Open this workout's week</span>
            </button>
            <Button
              aria-label="Next workout"
              type="button"
              variant="ghost"
              size="icon"
              disabled={!nextWorkout}
              onClick={() => {
                if (nextWorkout) {
                  navigate(`/workouts/${nextWorkout.id}`)
                }
              }}
            >
              <ChevronRight aria-hidden="true" size={20} />
            </Button>
          </div>
        </header>
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
