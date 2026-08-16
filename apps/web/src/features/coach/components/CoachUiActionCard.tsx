import { useEffect, useState } from "react";
import { Button } from "@/shared/components/ui";
import {
  createExercise,
  listExercises,
} from "@/features/training/api/trainingApi";
import { type MuscleGroup } from "@/features/training/constants/muscleGroups";
import { type Exercise } from "@/features/training/types";
import { AddExerciseDialog } from "@/features/training/components/AddExerciseDialog";
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
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [isLoadingExercises, setIsLoadingExercises] = useState(false);
  const [muscleGroupFilter, setMuscleGroupFilter] = useState<MuscleGroup>();
  useEffect(() => {
    if (mode === "none") return;
    setIsLoadingExercises(true);
    void listExercises({ muscleGroup: muscleGroupFilter }).then(setExercises).finally(() => setIsLoadingExercises(false));
  }, [mode, muscleGroupFilter]);
  if (action.status !== "pending")
    return (
      <p className="mt-2 text-xs text-muted-foreground">
        {action.status === "dismissed" ? "Dismissed." : "Exercise selected."}
      </p>
    );
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
      <AddExerciseDialog
        exercises={exercises}
        isLoading={isLoadingExercises}
        isCreating={disabled}
        muscleGroupFilter={muscleGroupFilter}
        open={mode !== "none"}
        intent={{
          kind: 'coach',
          onSelect: (exercise) => onResolve(exercise, 'selected'),
          onCreate: (exercise) => onResolve(exercise, 'created'),
        }}
        initialDefinition={{
          ...action.payload.draft_exercise,
          muscle_group: action.payload.draft_exercise.muscle_group as Exercise['muscle_group'],
        }}
        initialStep={mode === 'create' ? 'create' : 'search'}
        initialQuery={action.payload.requested_name}
        allowCreateFromSearch={false}
        onCreate={createExercise}
        onOpenChange={(open) => !open && setMode('none')}
        onMuscleGroupFilterChange={setMuscleGroupFilter}
      />
    </section>
  );
}
