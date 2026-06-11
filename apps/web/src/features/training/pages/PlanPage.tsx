import { getErrorMessage } from '../../../shared/api/errors'
import { InlineError } from '../../../shared/components/InlineError'
import { ScrollableStack } from '../../../shared/layout/ScrollableStack'
import { TrainingLayout } from '../../../shared/layout/TrainingLayout'
import { WorkoutListItemButton } from '../components/WorkoutListItemButton'
import { useTrainingPlanPage } from '../hooks/useTrainingPlanPage'

export function PlanPage() {
  const { selectedPlan, workoutItems, isLoading, error } = useTrainingPlanPage()

  return (
    <TrainingLayout>
      <section className="training-content">
        <div className="section-heading">
          <p className="eyebrow">Plan</p>
          <h1>{selectedPlan?.name ?? 'Training plan'}</h1>
        </div>
        {isLoading ? <p className="muted">Loading plan...</p> : null}
        <InlineError message={error ? getErrorMessage(error) : null} />
        {!isLoading && !selectedPlan ? (
          <p className="empty-state">No training plans are available yet.</p>
        ) : null}
        {!isLoading && selectedPlan ? (
          <ScrollableStack
            empty={<p className="empty-state">This plan has no workouts yet.</p>}
          >
            {workoutItems.map((workout) => (
              <WorkoutListItemButton key={workout.id} workout={workout} />
            ))}
          </ScrollableStack>
        ) : null}
      </section>
    </TrainingLayout>
  )
}
