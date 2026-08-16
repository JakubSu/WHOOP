import { useEffect, useMemo, useState } from "react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  Input,
  Label,
} from "@/shared/components/ui";
import {
  createExercise,
  listExercises,
  type ExerciseInput,
} from "@/features/training/api/trainingApi";
import { MUSCLE_GROUPS } from "@/features/training/constants/muscleGroups";
import { type Exercise } from "@/features/training/types";
import { type CoachUiAction } from "../types";

export function CoachUiActionCard({
  action,
  disabled,
  onResolve,
  onDismiss,
}: {
  action: CoachUiAction;
  disabled: boolean;
  onResolve: (exercise: Exercise, method: "created" | "selected") => void;
  onDismiss: () => void;
}) {
  const [mode, setMode] = useState<"none" | "search" | "create">("none");
  const [query, setQuery] = useState(action.payload.requested_name);
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [draft, setDraft] = useState<ExerciseInput>(
    () =>
      ({
        ...action.payload.draft_exercise,
        default_sets: action.payload.draft_exercise.default_sets ?? 0,
        default_reps: action.payload.draft_exercise.default_reps ?? 0,
        default_time: action.payload.draft_exercise.default_time ?? 0,
        default_weight: action.payload.draft_exercise.default_weight ?? null,
        default_weight_unit:
          action.payload.draft_exercise.default_weight_unit ?? "lb",
        notes: action.payload.draft_exercise.notes ?? "",
      }) as ExerciseInput,
  );
  const matching = useMemo(
    () =>
      exercises.filter((item) =>
        item.name.toLowerCase().includes(query.trim().toLowerCase()),
      ),
    [exercises, query],
  );
  useEffect(() => {
    if (mode === "search") void listExercises().then(setExercises);
  }, [mode]);
  if (action.status !== "pending")
    return (
      <p className="mt-2 text-xs text-muted-foreground">
        {action.status === "dismissed" ? "Dismissed." : "Exercise selected."}
      </p>
    );
  async function create(event: React.FormEvent) {
    event.preventDefault();
    const exercise = await createExercise(draft);
    onResolve(exercise, "created");
    setMode("none");
  }
  return (
    <section className="mt-3 rounded-lg border border-border bg-background p-3 text-sm">
      <p className="font-medium">
        I couldn’t find “{action.payload.requested_name}”.
      </p>
      <p className="mt-1 text-muted-foreground">
        Create it, or choose an existing exercise.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button size="sm" disabled={disabled} onClick={() => setMode("create")}>
          Create new exercise
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={disabled}
          onClick={() => setMode("search")}
        >
          Choose existing exercise
        </Button>
        <Button
          size="sm"
          variant="ghost"
          disabled={disabled}
          onClick={onDismiss}
        >
          Dismiss
        </Button>
      </div>
      <Dialog
        open={mode !== "none"}
        onOpenChange={(open) => !open && setMode("none")}
      >
        <DialogContent>
          <DialogTitle>
            {mode === "create" ? "Create exercise" : "Choose exercise"}
          </DialogTitle>
          {mode === "create" ? (
            <form className="mt-3 space-y-3" onSubmit={create}>
              <Field
                label="Name"
                value={draft.name}
                onChange={(name) => setDraft({ ...draft, name })}
              />
              <Label>Prescription type</Label>
              <select
                className="h-10 w-full rounded-md border px-3"
                value={draft.prescription_type}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    prescription_type: event.target
                      .value as Exercise["prescription_type"],
                  })
                }
              >
                <option value="strength">Strength</option>
                <option value="timed">Timed</option>
              </select>
              <Label>Muscle group</Label>
              <select
                className="h-10 w-full rounded-md border px-3"
                value={draft.muscle_group}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    muscle_group: event.target
                      .value as Exercise["muscle_group"],
                  })
                }
              >
                {MUSCLE_GROUPS.map((group) => (
                  <option key={group} value={group}>
                    {group.replace("_", " ")}
                  </option>
                ))}
              </select>
              <Button type="submit" disabled={disabled}>
                Create exercise
              </Button>
            </form>
          ) : (
            <div className="mt-3">
              <Input
                autoFocus
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />{" "}
              <div className="mt-3 grid gap-1">
                {matching.map((exercise) => (
                  <Button
                    key={exercise.id}
                    variant="ghost"
                    className="justify-start"
                    disabled={disabled}
                    onClick={() => {
                      onResolve(exercise, "selected");
                      setMode("none");
                    }}
                  >
                    {exercise.name}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </section>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <Label>{label}</Label>
      <Input
        className="mt-1"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}
