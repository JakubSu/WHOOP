export type Prescription =
  {
    type?: "reps" | "time";
    sets: number;
    reps?: number;
    seconds?: number;
    weight?: string | null;
    weight_unit?: string;
    note?: string;
  }

export type RecommendationOperation =
  | {
    id: string;
    status: 'pending';
    operation_type: 'add_exercise';
    display_text: string;
    reason: string;
    payload: {
      exercise_id: string;
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
  status: CoachRecommendationReference['status'];
  summary: string;
  reason: string;
  coach_card_snapshot: CoachCardSnapshot;
  operations: RecommendationOperation[]
  workouts: Array<{
    id: string
    title: string
    workout: { id: string; name: string; date: string; expected_time: number; exercise_count: number }
    exercises: Array<{
      id: string
      exercise: { id: string; name: string; muscle_group: string; prescription_type: string }
      sets: number
      reps: number
      time: number
      sort_order: number
      weight: string | null
      weight_unit: string
      note: string
    }>
  }>
}
import { type CoachCardSnapshot, type CoachRecommendationReference } from '../coach/types'
