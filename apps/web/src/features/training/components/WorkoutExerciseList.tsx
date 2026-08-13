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

type WorkoutExerciseListProps = {
  exercises: WorkoutExerciseDisplay[];
  draftExercises: DraftExercise[];
  isEditing: boolean;
  onUpdateExercise: (exercise: WorkoutExerciseDisplay) => void;
  onRemoveExercise: (exercise: WorkoutExerciseDisplay) => void;
  onReorder: (activeId: string, overId: string) => void;
  onOpenAddDialog: () => void;
};

export function WorkoutExerciseList({
  exercises,
  draftExercises,
  isEditing,
  onUpdateExercise,
  onRemoveExercise,
  onReorder,
  onOpenAddDialog,
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
        {exercises.map((exercise) => (
          <div key={exercise.id}>
            <ExerciseCard exercise={exercise} />
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
