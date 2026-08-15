import {
  type Exercise,
  type WorkoutExerciseDisplay,
} from "../../training/types";
import { type Recommendation, type RecommendationOperation } from "../types";
import { RecommendationOperationCard } from "./RecommendationOperationCard";

type Props = {
  recommendation: Recommendation;
  exercises: WorkoutExerciseDisplay[];
  library: Exercise[];
  placement: number;
  movedPreview?: boolean;
  addsOnly?: boolean;
  onSave: (operation: RecommendationOperation) => void;
  onAccept: (id: string) => void;
  onReject: (id: string) => void;
  savingId: string | null;
  acceptingId: string | null;
  rejectingId: string | null;
};
export function RecommendationPanel(props: Props) {
  const operations = props.recommendation.operations.filter(isExerciseOperation).filter((operation) =>
    props.addsOnly
      ? operation.operation_type === "add_exercise" &&
        operation.payload.position === 1
      : operation.operation_type !== "add_exercise" &&
        placement(operation, props.exercises, props.movedPreview) ===
          props.placement,
  );
  if (!operations.length) return null;
  return (
    <>
      {operations.map((operation) => (
        <RecommendationOperationCard
          key={operation.id}
          operation={operation}
          exercise={target(operation, props.exercises)}
          exerciseLibrary={props.library}
          movedPreview={props.movedPreview}
          onSave={props.onSave}
          onAccept={() => props.onAccept(operation.id)}
          onReject={() => props.onReject(operation.id)}
          isSaving={props.savingId === operation.id}
          isAccepting={props.acceptingId === operation.id}
          isRejecting={props.rejectingId === operation.id}
        />
      ))}
    </>
  );
}
function isExerciseOperation(operation: RecommendationOperation): operation is Extract<RecommendationOperation, { operation_type: "add_exercise" | "update_exercise" | "remove_exercise" }> {
  return operation.operation_type === "add_exercise" || operation.operation_type === "update_exercise" || operation.operation_type === "remove_exercise";
}
function placement(
  operation: Extract<RecommendationOperation, { operation_type: "add_exercise" | "update_exercise" | "remove_exercise" }>,
  exercises: WorkoutExerciseDisplay[],
  source: boolean | undefined,
) {
  if (operation.operation_type === "add_exercise")
    return source ? -99 : operation.payload.position - 1;
  const index = indexFor(operation.payload.workout_exercise_id, exercises);
  if (
    operation.operation_type === "update_exercise" &&
    operation.payload.position
  )
    return source ? index : operation.payload.position - 1;
  return source ? -99 : index;
}
function target(
  operation: Extract<RecommendationOperation, { operation_type: "add_exercise" | "update_exercise" | "remove_exercise" }>,
  exercises: WorkoutExerciseDisplay[],
) {
  return operation.operation_type === "add_exercise"
    ? undefined
    : exercises[indexFor(operation.payload.workout_exercise_id, exercises)];
}
function indexFor(id: string, exercises: WorkoutExerciseDisplay[]) {
  const found = exercises.findIndex((exercise) => exercise.id === id);
  if (found >= 0) return found;
  if (id === "first-exercise") return 0;
  if (id === "second-exercise") return Math.min(1, exercises.length - 1);
  return exercises.length - 1;
}
