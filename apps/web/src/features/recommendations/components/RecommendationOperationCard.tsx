import { useState } from "react";
import { Check, Pencil, X } from "lucide-react";
import {
  type Exercise,
  type WorkoutExerciseDisplay,
} from "../../training/types";
import { type Prescription, type RecommendationOperation } from "../types";
import { updateChangeEntries } from "../services/operationChanges";

type ExerciseRecommendationOperation = Extract<RecommendationOperation, { operation_type: "add_exercise" | "update_exercise" | "remove_exercise" }>;

type Props = {
  operation: ExerciseRecommendationOperation;
  exercise: WorkoutExerciseDisplay | undefined;
  exerciseLibrary: Exercise[];
  onSave: (operation: RecommendationOperation) => void;
  onAccept: () => void;
  onReject: () => void;
  isSaving: boolean;
  isAccepting: boolean;
  isRejecting: boolean;
  movedPreview?: boolean;
};
const labels: Record<string, string> = {
  sets: "Sets",
  reps: "Reps",
  seconds: "Time",
  weight: "Weight",
  weight_unit: "Unit",
  note: "Note",
};

export function RecommendationOperationCard(props: Props) {
  const [draft, setDraft] = useState<ExerciseRecommendationOperation | null>(null);
  const operation = draft ?? props.operation;
  const editing = Boolean(draft);
  const busy = props.isSaving || props.isAccepting || props.isRejecting;
  if (
    props.movedPreview &&
    props.operation.operation_type === "update_exercise"
  )
    return (
      <div className="recommendation-source">
        <span>MOVE</span>
        <del>
          {props.exercise?.exerciseName ?? props.operation.display_text}
        </del>
        <small>Position {positionOf(props.exercise)}</small>
      </div>
    );
  return (
    <article
      className={`recommendation-row recommendation-row--${props.operation.operation_type}`}
    >
      <header>
        <span className="recommendation-tag">
          {tagFor(props.operation.operation_type)}
        </span>
        <strong>
          {props.operation.operation_type === "add_exercise"
            ? exerciseName(props.operation, props.exerciseLibrary)
            : (props.exercise?.exerciseName ?? operation.display_text)}
        </strong>
      </header>
      {operation.operation_type === "remove_exercise" ? (
        <del>{props.exercise?.prescription ?? operation.display_text}</del>
      ) : operation.operation_type === "add_exercise" ? (
        <Proposal
          operation={operation}
          library={props.exerciseLibrary}
          editing={editing}
          onChange={setDraft}
        />
      ) : (
        <Update
          operation={operation}
          exercise={props.exercise}
          editing={editing}
          onChange={setDraft}
        />
      )}
      <small>{props.operation.reason}</small>
      <footer>
        {props.operation.operation_type !== "remove_exercise" &&
          (editing ? (
            <>
              <button
                type="button"
                onClick={() => setDraft(null)}
                disabled={busy}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => props.onSave(operation)}
                disabled={busy}
              >
                Save
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => setDraft(props.operation)}
              disabled={busy}
            >
              <Pencil size={14} /> Edit
            </button>
          ))}
        <button
          type="button"
          onClick={props.onAccept}
          disabled={busy || editing}
        >
          <Check size={14} /> Accept
        </button>
        <button
          type="button"
          onClick={props.onReject}
          disabled={busy || editing}
        >
          <X size={14} /> Reject
        </button>
      </footer>
    </article>
  );
}

function Proposal({
  operation,
  library,
  editing,
  onChange,
}: {
  operation: Extract<
    RecommendationOperation,
    { operation_type: "add_exercise" }
  >;
  library: Exercise[];
  editing: boolean;
  onChange: (operation: ExerciseRecommendationOperation) => void;
}) {
  const prescription = operation.payload.prescription;
  const update = (changes: Partial<Prescription>) =>
    onChange({
      ...operation,
      payload: {
        ...operation.payload,
        prescription: { ...prescription, ...changes },
      },
    });
  return (
    <div className="recommendation-details">
      {editing ? (
        <select
          value={operation.payload.exercise_id}
          onChange={(event) => {
            const exercise = library.find(
              (item) => item.id === event.target.value,
            );
            if (exercise)
              onChange({
                ...operation,
                payload: {
                  ...operation.payload,
                  exercise_id: exercise.id,
                },
              });
          }}
        >
          {library.map((exercise) => (
            <option key={exercise.id} value={exercise.id}>
              {exercise.name}
            </option>
          ))}
        </select>
      ) : null}
      <PrescriptionView
        values={prescription}
        editable={editing}
        onChange={update}
      />
      {editing ? (
        <label>
          Position{" "}
          <input
            type="number"
            min="1"
            value={operation.payload.position}
            onChange={(event) =>
              onChange({
                ...operation,
                payload: {
                  ...operation.payload,
                  position: Number(event.target.value),
                },
              })
            }
          />
        </label>
      ) : (
        <span>Position {operation.payload.position}</span>
      )}
    </div>
  );
}
function Update({
  operation,
  exercise,
  editing,
  onChange,
}: {
  operation: Extract<
    RecommendationOperation,
    { operation_type: "update_exercise" }
  >;
  exercise: WorkoutExerciseDisplay | undefined;
  editing: boolean;
  onChange: (operation: ExerciseRecommendationOperation) => void;
}) {
  const changes = operation.payload.changes ?? {};
  return (
    <div className="recommendation-details">
      {updateChangeEntries(changes).map(([field, value]) => (
        <label key={field}>
          {labels[field] ?? field}
          <del>
            {String(exercise?.[field as keyof WorkoutExerciseDisplay] ?? "—")}
          </del>
          {editing ? (
            <input
              value={String(value ?? "")}
              onChange={(event) =>
                onChange({
                  ...operation,
                  payload: {
                    ...operation.payload,
                    changes: {
                      ...changes,
                      [field]:
                        field === "weight" ||
                        field === "note" ||
                        field === "weight_unit"
                          ? event.target.value
                          : Number(event.target.value),
                    },
                  },
                })
              }
            />
          ) : (
            <ins>{String(value)}</ins>
          )}
        </label>
      ))}
      {operation.payload.position ? (
        editing ? (
          <label>
            New position{" "}
            <input
              type="number"
              min="1"
              value={operation.payload.position}
              onChange={(event) =>
                onChange({
                  ...operation,
                  payload: {
                    ...operation.payload,
                    position: Number(event.target.value),
                  },
                })
              }
            />
          </label>
        ) : (
          <span>Moved to position {operation.payload.position}</span>
        )
      ) : null}
    </div>
  );
}
function PrescriptionView({
  values,
  editable,
  onChange,
}: {
  values: Prescription;
  editable: boolean;
  onChange: (changes: Partial<Prescription>) => void;
}) {
  return (
    <>
      {(values.type === "duration"
        ? (["seconds"] as const)
        : values.type === "time"
        ? (["sets", "seconds"] as const)
        : (["sets", "reps", "weight"] as const)
      ).map((field) => (
        <label key={field}>
          {labels[field]}
          {editable ? (
            <input
                value={values[field] ?? ""}
                onChange={(event) =>
                  onChange({
                    [field]:
                      field === "weight"
                      ? event.target.value
                      : Number(event.target.value),
                })
              }
            />
          ) : (
            <span>{values[field] || "—"}</span>
          )}
        </label>
      ))}
    </>
  );
}
function tagFor(type: Props["operation"]["operation_type"]) {
  return type === "add_exercise"
    ? "+ ADD"
    : type === "remove_exercise"
      ? "REMOVE"
      : "MODIFY";
}
function exerciseName(
  operation: Extract<
    RecommendationOperation,
    { operation_type: "add_exercise" }
  >,
  library: Exercise[],
) {
  return (
    library.find((exercise) => exercise.id === operation.payload.exercise_id)
      ?.name ?? operation.display_text
  );
}
function positionOf(exercise: WorkoutExerciseDisplay | undefined) {
  return (exercise?.sort_order ?? 0) + 1;
}
