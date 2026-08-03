import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Plus } from "lucide-react";
import { type WorkoutExerciseDisplay } from "../types";
import { type DraftExercise } from "../hooks/useWorkoutEditor";
import { ExerciseCard } from "./ExerciseCard";
import { RecommendationPanel } from "../../recommendations/components/RecommendationPanel";
import { type Exercise } from "../types";
import {
  type Recommendation,
  type RecommendationOperation,
} from "../../recommendations/types";

type WorkoutExerciseListProps = {
  exercises: WorkoutExerciseDisplay[];
  draftExercises: DraftExercise[];
  isEditing: boolean;
  onUpdateExercise: (exercise: WorkoutExerciseDisplay) => void;
  onRemoveExercise: (exercise: WorkoutExerciseDisplay) => void;
  onReorder: (activeId: string, overId: string) => void;
  onOpenAddDialog: () => void;
  recommendation: Recommendation | null;
  recommendationLibrary: Exercise[];
  onSaveRecommendation: (operation: RecommendationOperation) => void;
  onAcceptRecommendation: (id: string) => void;
  onRejectRecommendation: (id: string) => void;
  savingRecommendationId: string | null;
  acceptingRecommendationId: string | null;
  rejectingRecommendationId: string | null;
};

export function WorkoutExerciseList({
  exercises,
  draftExercises,
  isEditing,
  onUpdateExercise,
  onRemoveExercise,
  onReorder,
  onOpenAddDialog,
  recommendation,
  recommendationLibrary,
  onSaveRecommendation,
  onAcceptRecommendation,
  onRejectRecommendation,
  savingRecommendationId,
  acceptingRecommendationId,
  rejectingRecommendationId,
}: WorkoutExerciseListProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  if (!isEditing) {
    return (
      <>
        {recommendation ? (
          <RecommendationPanel
            recommendation={recommendation}
            exercises={exercises}
            library={recommendationLibrary}
            placement={0}
            addsOnly
            onSave={onSaveRecommendation}
            onAccept={onAcceptRecommendation}
            onReject={onRejectRecommendation}
            savingId={savingRecommendationId}
            acceptingId={acceptingRecommendationId}
            rejectingId={rejectingRecommendationId}
          />
        ) : null}
        {exercises.map((exercise, index) => (
          <div key={exercise.id}>
            {recommendation ? (
              <RecommendationPanel
                recommendation={recommendation}
                exercises={exercises}
                library={recommendationLibrary}
                placement={index}
                movedPreview
                onSave={onSaveRecommendation}
                onAccept={onAcceptRecommendation}
                onReject={onRejectRecommendation}
                savingId={savingRecommendationId}
                acceptingId={acceptingRecommendationId}
                rejectingId={rejectingRecommendationId}
              />
            ) : null}
            {isMovedFrom(index, recommendation, exercises) ? null : (
              <ExerciseCard exercise={exercise} />
            )}
            {recommendation ? (
              <RecommendationPanel
                recommendation={recommendation}
                exercises={exercises}
                library={recommendationLibrary}
                placement={index}
                onSave={onSaveRecommendation}
                onAccept={onAcceptRecommendation}
                onReject={onRejectRecommendation}
                savingId={savingRecommendationId}
                acceptingId={acceptingRecommendationId}
                rejectingId={rejectingRecommendationId}
              />
            ) : null}
          </div>
        ))}
      </>
    );
  }

  function handleDragEnd(event: DragEndEvent) {
    if (event.over) onReorder(String(event.active.id), String(event.over.id));
  }

  return (
    <>
      <DndContext
        collisionDetection={closestCenter}
        sensors={sensors}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={draftExercises.map((exercise) => exercise.id)}
          strategy={verticalListSortingStrategy}
        >
          {draftExercises.map((exercise) => (
            <SortableExerciseCard
              key={exercise.id}
              exercise={exercise}
              onChange={onUpdateExercise}
              onDelete={onRemoveExercise}
            />
          ))}
        </SortableContext>
      </DndContext>
      <button
        className="flex w-full flex-col items-center gap-2 rounded-lg border border-dashed border-muted-foreground/40 py-7 text-muted-foreground transition-colors hover:border-primary hover:bg-accent hover:text-foreground"
        type="button"
        onClick={onOpenAddDialog}
      >
        <Plus aria-hidden="true" size={27} />
        <span className="text-xs font-bold uppercase tracking-[0.16em]">
          Add exercise
        </span>
      </button>
    </>
  );
}

function isMovedFrom(
  index: number,
  recommendation: Recommendation | null,
  exercises: WorkoutExerciseDisplay[],
) {
  return Boolean(
    recommendation?.operations.some(
      (operation) =>
        operation.operation_type === "update_exercise" &&
        operation.payload.position &&
        targetIndex(operation.payload.workout_exercise_id, exercises) === index,
    ),
  );
}

function targetIndex(id: string, exercises: WorkoutExerciseDisplay[]) {
  const found = exercises.findIndex((exercise) => exercise.id === id);
  if (found >= 0) return found;
  if (id === "first-exercise") return 0;
  if (id === "second-exercise") return Math.min(1, exercises.length - 1);
  return exercises.length - 1;
}

function SortableExerciseCard({
  exercise,
  onChange,
  onDelete,
}: {
  exercise: DraftExercise;
  onChange: (exercise: WorkoutExerciseDisplay) => void;
  onDelete: (exercise: WorkoutExerciseDisplay) => void;
}) {
  const {
    attributes,
    listeners,
    setActivatorNodeRef,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: exercise.id });

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      {...attributes}
    >
      <ExerciseCard
        editable
        exercise={exercise}
        dragHandleProps={listeners}
        dragHandleRef={setActivatorNodeRef}
        onChange={onChange}
        onDelete={onDelete}
      />
    </div>
  );
}
