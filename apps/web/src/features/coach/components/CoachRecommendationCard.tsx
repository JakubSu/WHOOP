import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, LoaderCircle } from "lucide-react";
import {
  getWorkout,
  listWorkoutExercises,
} from "../../training/api/trainingApi";
import {
  type Exercise,
  type WorkoutExerciseDisplay,
} from "../../training/types";
import { buildExerciseDisplays } from "../../training/services/formatters";
import { RecommendationOperationCard } from "../../recommendations/components/RecommendationOperationCard";
import { useRecommendation } from "../../recommendations/hooks/useWorkoutRecommendation";
import {
  type Recommendation,
  type RecommendationGroup,
  type RecommendationOperation,
} from "../../recommendations/types";
import {
  buildDraftExercises,
  groupTargetKey,
} from "../../recommendations/services/workoutCard";
import { useProductTour } from "../../product-tour/ProductTourProvider";
import { type CoachRecommendationReference } from "../types";

type Props = { recommendation: CoachRecommendationReference };

export function CoachRecommendationCard({ recommendation }: Props) {
  return (
    <RecommendationCardDetail
      recommendationId={recommendation.id}
      fallback={recommendation}
    />
  );
}

function RecommendationCardDetail({
  recommendationId,
  fallback,
}: {
  recommendationId: string;
  fallback: CoachRecommendationReference;
}) {
  const [expanded, setExpanded] = useState(true);
  const { guidedCoachStage, notifyGuidedRecommendationExpanded, notifyGuidedRecommendationAccepted } = useProductTour();
  const detail = useRecommendation(recommendationId, undefined, fallback.actionable);
  const recommendation = detail.recommendation;

  if (!fallback.actionable)
    return <HistoricalRecommendationCard recommendation={fallback} />;
  if (!recommendation) return <LoadingCard />;
  const pending = recommendation.operations.filter(
    (operation) => operation.status === "pending",
  ).length;
  // Never trust a retained card alone: a recommendation can become historical
  // between rendering the chat and loading its detail.
  const actionable =
    recommendation.status === "active" && pending > 0;
  const readOnly = !actionable;

  return (
    <section
      className="mt-3 overflow-hidden rounded-lg border border-primary/30 bg-background"
      aria-label="Coach recommendation"
      data-tour={guidedCoachStage === 'review_replacement' ? 'coach-replacement-recommendation' : 'coach-recommendation-card'}
    >
      <button
        className="flex w-full items-center justify-between gap-3 px-3 py-3 text-left"
        type="button"
        onClick={() => {
          const nextExpanded = !expanded;
          setExpanded(nextExpanded);
          if (nextExpanded) notifyGuidedRecommendationExpanded();
        }}
        aria-expanded={expanded}
        data-tour="coach-recommendation-toggle"
      >
        <span>
          <strong className="block text-sm">Training recommendation</strong>
          <span className="text-xs text-muted-foreground">
            {readOnly
              ? "Applied workout changes"
              : `${pending} pending change${pending === 1 ? "" : "s"}`}
          </span>
        </span>
        <ChevronDown
          className={
            expanded
              ? "rotate-180 transition-transform"
              : "transition-transform"
          }
          size={18}
        />
      </button>
      {expanded ? (
        <div className="grid gap-3 border-t border-border p-3" data-tour="coach-recommendation-details">
          {recommendation.groups.map((group) => (
            <WorkoutRecommendationCard
              key={group.id}
              group={group}
              recommendation={recommendation}
              detail={detail}
              readOnly={readOnly}
            />
          ))}
          {!readOnly ? (
            <div className="flex flex-wrap gap-2 border-t border-border pt-3">
              <button
                className="rounded bg-primary px-2 py-1 text-xs text-primary-foreground"
                type="button"
                data-tour="coach-accept-all"
                disabled={detail.isBulkAccepting}
                onClick={() =>
                  void detail.acceptAll().then(() => {
                    notifyGuidedRecommendationAccepted();
                  })
                }
              >
                Accept all
              </button>
              <button
                className="rounded border px-2 py-1 text-xs"
                type="button"
                disabled={detail.isBulkRejecting}
                onClick={() => void detail.rejectAll()}
              >
                Reject all
              </button>
            </div>
          ) : null}
          {detail.error ? (
            <p className="text-xs text-destructive">
              Could not update this recommendation. Try again.
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function WorkoutRecommendationCard({
  group,
  recommendation,
  detail,
  readOnly,
}: {
  group: RecommendationGroup;
  recommendation: Recommendation;
  detail: ReturnType<typeof useRecommendation>;
  readOnly: boolean;
}) {
  const { guidedCoachStage } = useProductTour();
  const [expanded, setExpanded] = useState(false);
  useEffect(() => {
    if (
      (group.target.kind === "new" && guidedCoachStage === "review_initial") ||
      guidedCoachStage === "review_replacement"
    ) {
      setExpanded(true);
    }
  }, [group.target.kind, guidedCoachStage]);
  const operations = recommendation.operations.filter((operation) =>
    group.operation_ids.includes(operation.id),
  );
  const workoutOperation = operations.find((operation) =>
    operation.operation_type.endsWith("_workout"),
  );
  const hidden =
    (workoutOperation?.operation_type === "remove_workout" &&
      workoutOperation.status === "accepted") ||
    (group.target.kind === "new" && workoutOperation?.status === "rejected");
  if (hidden) return null;
  return (
    <details
      className="rounded-md border bg-card"
      open={expanded}
      data-tour={
        group.target.kind === "new"
          ? "coach-generated-workout-recommendation"
          : undefined
      }
      onToggle={(event) =>
        setExpanded((event.currentTarget as HTMLDetailsElement).open)
      }
    >
      <summary className="cursor-pointer px-3 py-3 text-sm font-medium">
        {group.title}
        <span className="ml-2 font-normal text-muted-foreground">
          {operations.filter((operation) => operation.status === "pending")
            .length
            ? "Pending changes"
            : "Workout"}
        </span>
      </summary>
      {workoutOperation?.operation_type === "update_workout" &&
      workoutOperation.status === "pending" ? (
        <div className="border-t border-border px-3 py-2">
          <WorkoutChange
            operation={workoutOperation}
            detail={detail}
            readOnly={readOnly}
          />
        </div>
      ) : null}
      {workoutOperation?.operation_type === "remove_workout" &&
      workoutOperation.status === "pending" ? (
        <div className="border-t border-border px-3 py-2">
          <WholeWorkoutAction
            label="Delete workout"
            operation={workoutOperation}
            detail={detail}
            readOnly={readOnly}
          />
        </div>
      ) : null}
      {workoutOperation?.operation_type === "add_workout" &&
      workoutOperation.status === "pending" ? (
        <div className="border-t border-border px-3 py-2">
          <WholeWorkoutAction
            label="Add workout"
            operation={workoutOperation}
            detail={detail}
            readOnly={readOnly}
          />
        </div>
      ) : null}
      <div className="grid gap-3 border-t border-border p-3">
        <WorkoutRecommendationBody
          group={group}
          operations={operations}
          detail={detail}
          readOnly={readOnly}
        />
      </div>
    </details>
  );
}

function WorkoutRecommendationBody({
  group,
  operations,
  detail,
  readOnly,
}: {
  group: RecommendationGroup;
  operations: RecommendationOperation[];
  detail: ReturnType<typeof useRecommendation>;
  readOnly: boolean;
}) {
  const workoutOperation = operations.find(
    (operation) =>
      operation.operation_type === "add_workout" ||
      operation.operation_type === "update_workout" ||
      operation.operation_type === "remove_workout",
  );
  const isNewWholeWorkout = workoutOperation?.operation_type === "add_workout";
  const workout = useWorkoutCardData(group, operations, detail.exerciseLibrary);
  if (workout.isLoading)
    return (
      <p className="flex items-center gap-2 text-xs text-muted-foreground">
        <LoaderCircle className="size-3 animate-spin" /> Loading workout…
      </p>
    );
  if (!workout.data) return null;
  return (
    <>
      <div className="text-xs text-muted-foreground">
        {workout.data.date} · {workout.data.expected_time ?? 0} min
      </div>
      <ul className="grid gap-2">
        {workout.data.exercises.map((exercise) => (
          <ExerciseRecommendationRow
            key={exercise.id}
            exercise={exercise}
            operations={operations}
            detail={detail}
            readOnly={readOnly || Boolean(isNewWholeWorkout)}
          />
        ))}
      </ul>
      {isNewWholeWorkout
        ? null
        : operations
            .filter(
              (
                operation,
              ): operation is Extract<
                RecommendationOperation,
                { operation_type: "add_exercise" }
              > =>
                operation.operation_type === "add_exercise" &&
                operation.status === "pending",
            )
            .map((operation) => (
              <RecommendationOperationCard
                key={operation.id}
                operation={operation}
                exercise={undefined}
                exerciseLibrary={detail.exerciseLibrary}
                onSave={detail.saveOperation}
                onAccept={() => void detail.acceptOperation(operation.id)}
                onReject={() => void detail.rejectOperation(operation.id)}
                isSaving={detail.savingOperationId === operation.id}
                isAccepting={detail.acceptingOperationId === operation.id}
                isRejecting={detail.rejectingOperationId === operation.id}
              />
            ))}
    </>
  );
}

function ExerciseRecommendationRow({
  exercise,
  operations,
  detail,
  readOnly,
}: {
  exercise: WorkoutExerciseDisplay;
  operations: RecommendationOperation[];
  detail: ReturnType<typeof useRecommendation>;
  readOnly: boolean;
}) {
  const operation = operations.find(
    (
      item,
    ): item is Extract<
      RecommendationOperation,
      { operation_type: "update_exercise" | "remove_exercise" }
    > =>
      (item.operation_type === "update_exercise" ||
        item.operation_type === "remove_exercise") &&
      item.payload.workout_exercise_id === exercise.id &&
      item.status === "pending",
  );
  return (
    <li className="rounded border border-border/70 p-2 text-xs">
      <p className="font-medium">{exercise.exerciseName}</p>
      <p className="text-muted-foreground">{exercise.prescription}</p>
      {operation && !readOnly ? (
        <RecommendationOperationCard
          operation={operation}
          exercise={exercise}
          exerciseLibrary={detail.exerciseLibrary}
          onSave={detail.saveOperation}
          onAccept={() => void detail.acceptOperation(operation.id)}
          onReject={() => void detail.rejectOperation(operation.id)}
          isSaving={detail.savingOperationId === operation.id}
          isAccepting={detail.acceptingOperationId === operation.id}
          isRejecting={detail.rejectingOperationId === operation.id}
        />
      ) : null}
    </li>
  );
}

function WorkoutChange({
  operation,
  detail,
  readOnly,
}: {
  operation: Extract<
    RecommendationOperation,
    { operation_type: "update_workout" }
  >;
  detail: ReturnType<typeof useRecommendation>;
  readOnly: boolean;
}) {
  return (
    <div className="rounded border border-primary/30 p-2 text-xs">
      <p className="font-medium">Update workout</p>
      <p className="mt-1 text-muted-foreground">
        {Object.entries(operation.payload.changes)
          .map(([field, value]) => `${field}: ${value}`)
          .join(" · ")}
      </p>
      <ActionButtons operation={operation} detail={detail} readOnly={readOnly} />
    </div>
  );
}

function WholeWorkoutAction({
  label,
  operation,
  detail,
  readOnly,
}: {
  label: string;
  operation: Extract<
    RecommendationOperation,
    { operation_type: "add_workout" | "remove_workout" }
  >;
  detail: ReturnType<typeof useRecommendation>;
  readOnly: boolean;
}) {
  return (
    <div className="rounded border border-primary/30 bg-primary/5 p-2 text-xs">
      <p className="font-medium">{label}</p>
      <p className="mt-1 text-muted-foreground">{operation.reason}</p>
      <ActionButtons operation={operation} detail={detail} readOnly={readOnly} />
    </div>
  );
}

function ActionButtons({
  operation,
  detail,
  readOnly,
}: {
  operation: RecommendationOperation;
  detail: ReturnType<typeof useRecommendation>;
  readOnly: boolean;
}) {
  const busy =
    detail.acceptingOperationId === operation.id ||
    detail.rejectingOperationId === operation.id;
  if (readOnly || operation.status !== "pending") return null;
  return (
    <div className="mt-2 flex gap-2">
      <button
        className="rounded bg-primary px-2 py-1 text-primary-foreground"
        type="button"
        disabled={busy}
        onClick={() => void detail.acceptOperation(operation.id)}
      >
        Accept
      </button>
      <button
        className="rounded border px-2 py-1"
        type="button"
        disabled={busy}
        onClick={() => void detail.rejectOperation(operation.id)}
      >
        Reject
      </button>
    </div>
  );
}

function useWorkoutCardData(
  group: RecommendationGroup,
  operations: RecommendationOperation[],
  library: Exercise[],
) {
  const targetKey = groupTargetKey(group);
  const workout = useQuery({
    queryKey: ["workout", targetKey],
    queryFn: () =>
      getWorkout(
        group.target.kind === "existing" ? group.target.workout_id : "",
      ),
    enabled: group.target.kind === "existing",
  });
  const exercises = useQuery({
    queryKey: ["workout-exercises", targetKey],
    queryFn: () =>
      listWorkoutExercises(
        group.target.kind === "existing" ? group.target.workout_id : "",
      ),
    enabled: group.target.kind === "existing",
  });
  if (group.target.kind === "new") {
    return {
      isLoading: false,
      data: {
        ...group.target.draft,
        exercises: buildDraftExercises(operations, library),
      },
    };
  }
  return {
    isLoading: workout.isLoading || exercises.isLoading,
    data: workout.data
      ? {
          ...workout.data,
          exercises: buildExerciseDisplays(exercises.data ?? []),
        }
      : null,
  };
}

function LoadingCard() {
  return (
    <section className="mt-3 rounded-lg border border-primary/30 bg-background px-3 py-3 text-xs text-muted-foreground">
      <LoaderCircle className="mr-2 inline size-3 animate-spin" /> Loading
      recommendation…
    </section>
  );
}

function HistoricalRecommendationCard(_props: Props) {
  return (
    <section className="mt-3 rounded-lg border border-border bg-muted/30 px-3 py-3">
      <strong className="block text-sm">Training recommendation</strong>
      <p className="mt-1 text-xs text-muted-foreground">
        Resolved workout changes
      </p>
    </section>
  );
}
