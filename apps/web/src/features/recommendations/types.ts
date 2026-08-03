export type Prescription =
  {
    sets: number;
    reps: number;
    time: number;
    weight: string | null;
    weight_unit: string;
    note: string
  }

type ExerciseRef = {
  id: string;
  name: string
}

export type RecommendationOperation =
  | {
    id: string;
    status: 'pending';
    operation_type: 'add_exercise';
    display_text: string;
    reason: string;
    payload: {
      exercise: ExerciseRef;
      prescription: Prescription;
      position: number
    }
  }
  | {
    id: string;
    status: 'pending';
    operation_type: 'update_exercise';
    display_text: string;
    reason: string;
    payload: {
      workout_exercise_id: string;
      changes: Partial<Prescription>;
      position?: number
    }
  }
  | {
    id: string;
    status: 'pending';
    operation_type: 'remove_exercise';
    display_text: string;
    reason: string;
    payload: { workout_exercise_id: string }
  }

export type Recommendation = {
  id: string;
  workout_id: string;
  summary: string;
  reason: string;
  operations: RecommendationOperation[]
}
