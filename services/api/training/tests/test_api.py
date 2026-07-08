from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from training.models import Exercise, TrainingPlan, Workout, WorkoutExercise


class TrainingApiOwnershipTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = cast(Any, User.objects).create_user(
            email="one@example.com", password="strong-password"
        )
        self.other_user = cast(Any, User.objects).create_user(
            email="two@example.com", password="strong-password"
        )
        client = APIClient()
        client.force_authenticate(self.user)
        self.client = client

    def test_workout_create_uses_authenticated_user_id(self) -> None:
        response = self.client.post(
            reverse("workout-collection"),
            {"name": "Upper Body", "user_id": str(self.other_user.id)},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        workout = Workout.objects.get(name="Upper Body", user_id=str(self.user.id))
        self.assertEqual(workout.user_id, str(self.user.id))
        self.assertNotIn("user_id", response.json())

    def test_workout_list_is_scoped_to_authenticated_user(self) -> None:
        Workout.objects.create(name="Mine", user_id=str(self.user.id))
        Workout.objects.create(name="Theirs", user_id=str(self.other_user.id))

        response = self.client.get(reverse("workout-collection"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["name"], "Mine")

    def test_detail_does_not_return_other_user_workout(self) -> None:
        workout = Workout.objects.create(name="Theirs", user_id=str(self.other_user.id))

        response = self.client.get(reverse("workout-detail", args=[workout.id]))

        self.assertEqual(response.status_code, 404)

    def test_training_endpoints_require_authentication(self) -> None:
        client = APIClient()

        response = cast(Any, client.get(reverse("workout-collection")))

        self.assertEqual(response.status_code, 401)


class MinimalTrainingApiTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = cast(Any, User.objects).create_user(
            email="minimal@example.com",
            password="strong-password",
        )
        client = APIClient()
        client.force_authenticate(self.user)
        self.client = client

    def test_create_minimal_training_flow(self) -> None:
        plan_response = self.client.post(
            reverse("training-plan-collection"),
            {"name": "Summer Block", "start_date": "2026-06-01", "end_date": "2026-07-01"},
            format="json",
        )
        self.assertEqual(plan_response.status_code, 201)
        self.assertEqual(
            set(plan_response.json().keys()),
            {"id", "name", "start_date", "end_date"},
        )

        workout_response = self.client.post(
            reverse("workout-collection"),
            {
                "plan": plan_response.json()["id"],
                "name": "Upper Body",
                "date": "2026-06-09",
                "expected_time": 45,
            },
            format="json",
        )
        self.assertEqual(workout_response.status_code, 201)
        self.assertEqual(
            set(workout_response.json().keys()),
            {"id", "plan", "name", "date", "expected_time"},
        )

        exercise_response = self.client.post(
            reverse("exercise-collection"),
            {
                "name": "Bench Press",
                "default_sets": 4,
                "default_reps": 8,
                "muscle_group": "Chest",
                "default_time": 0,
                "notes": "Pause reps.",
            },
            format="json",
        )
        self.assertEqual(exercise_response.status_code, 201)
        self.assertEqual(
            set(exercise_response.json().keys()),
            {
                "id",
                "name",
                "prescription_type",
                "default_sets",
                "default_reps",
                "muscle_group",
                "default_time",
                "notes",
            },
        )

        workout_exercise_response = self.client.post(
            reverse("workout-exercise-collection"),
            {
                "workout": workout_response.json()["id"],
                "exercise": exercise_response.json()["id"],
                "sets": 4,
                "reps": 8,
                "weight": "135.00",
                "weight_unit": "lb",
                "note": "Move well.",
            },
            format="json",
        )
        self.assertEqual(workout_exercise_response.status_code, 201)
        self.assertEqual(
            set(workout_exercise_response.json().keys()),
            {"id", "workout", "exercise", "sets", "reps", "time", "weight", "weight_unit", "note"},
        )

    def test_patch_workout_exercise_minimal_fields(self) -> None:
        workout = Workout.objects.create(name="Upper Body", user_id=str(self.user.id))
        exercise = Exercise.objects.create(name="Bench Press", user_id=str(self.user.id))
        workout_exercise = WorkoutExercise.objects.create(workout=workout, exercise=exercise)

        response = self.client.patch(
            reverse("workout-exercise-detail", args=[workout_exercise.id]),
            {"sets": 5, "reps": 6, "weight": "155.50", "weight_unit": "lb", "note": "Top set."},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["sets"], 5)
        self.assertEqual(body["reps"], 6)
        self.assertEqual(body["weight"], "155.50")
        self.assertEqual(body["weight_unit"], "lb")
        self.assertEqual(body["note"], "Top set.")

    def test_strength_workout_exercise_rejects_time(self) -> None:
        workout = Workout.objects.create(name="Upper Body", user_id=str(self.user.id))
        exercise = Exercise.objects.create(name="Bench Press", user_id=str(self.user.id))

        response = self.client.post(
            reverse("workout-exercise-collection"),
            {
                "workout": str(workout.id),
                "exercise": str(exercise.id),
                "sets": 4,
                "reps": 8,
                "time": 20,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_timed_workout_exercise_accepts_time(self) -> None:
        workout = Workout.objects.create(name="Core", user_id=str(self.user.id))
        exercise = Exercise.objects.create(
            name="Plank",
            prescription_type=Exercise.PrescriptionType.TIMED,
            user_id=str(self.user.id),
        )

        response = self.client.post(
            reverse("workout-exercise-collection"),
            {
                "workout": str(workout.id),
                "exercise": str(exercise.id),
                "time": 45,
                "note": "Brace.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["time"], 45)

    def test_plan_workouts_returns_only_requested_plan_with_exercise_counts(self) -> None:
        plan = TrainingPlan.objects.create(name="Summer Block", user_id=str(self.user.id))
        User = get_user_model()
        other_user = cast(Any, User.objects).create_user(
            email="third@example.com",
            password="strong-password",
        )
        other_plan = TrainingPlan.objects.create(name="Other Block", user_id=str(other_user.id))
        workout = Workout.objects.create(
            name="Upper Body",
            user_id=str(self.user.id),
            plan=plan,
            date="2026-06-10",
            expected_time=45,
        )
        Workout.objects.create(
            name="Conditioning",
            user_id=str(other_user.id),
            plan=other_plan,
            date="2026-06-11",
            expected_time=30,
        )
        exercise_one = Exercise.objects.create(name="Bench Press", user_id=str(self.user.id))
        exercise_two = Exercise.objects.create(name="Row", user_id=str(self.user.id))
        WorkoutExercise.objects.create(workout=workout, exercise=exercise_one)
        WorkoutExercise.objects.create(workout=workout, exercise=exercise_two)

        response = self.client.get(reverse("training-plan-workout-collection", args=[plan.id]))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["id"], str(workout.id))
        self.assertEqual(body[0]["exercise_count"], 2)
        self.assertEqual(body[0]["expected_time"], 45)

    def test_plan_workouts_return_ascending_schedule_order(self) -> None:
        plan = TrainingPlan.objects.create(name="Summer Block", user_id=str(self.user.id))
        Workout.objects.create(
            name="Day 3",
            user_id=str(self.user.id),
            plan=plan,
            date="2026-06-12",
        )
        Workout.objects.create(
            name="Day 1",
            user_id=str(self.user.id),
            plan=plan,
            date="2026-06-10",
        )
        Workout.objects.create(
            name="Day 2",
            user_id=str(self.user.id),
            plan=plan,
            date="2026-06-11",
        )

        response = self.client.get(reverse("training-plan-workout-collection", args=[plan.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [workout["name"] for workout in response.json()],
            ["Day 1", "Day 2", "Day 3"],
        )

    def test_workout_create_rejects_missing_date_for_planned_workout(self) -> None:
        plan = TrainingPlan.objects.create(name="Summer Block", user_id=str(self.user.id))

        response = self.client.post(
            reverse("workout-collection"),
            {
                "plan": str(plan.id),
                "name": "Upper Body",
                "expected_time": 45,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Planned workouts must have a date.")

    def test_training_plan_create_rejects_second_plan_for_same_user(self) -> None:
        TrainingPlan.objects.create(name="Existing Plan", user_id=str(self.user.id))

        response = self.client.post(
            reverse("training-plan-collection"),
            {"name": "Second Plan"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "User already has a training plan.")

    def test_workout_landing_returns_todays_workout(self) -> None:
        plan = TrainingPlan.objects.create(name="Summer Block", user_id=str(self.user.id))
        workout = Workout.objects.create(
            name="Today Lift",
            user_id=str(self.user.id),
            plan=plan,
            date="2026-06-10",
            expected_time=45,
        )

        response = self.client.get(
            reverse("workout-landing"),
            {"today": "2026-06-10"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["selected_workout"]["id"], str(workout.id))
        self.assertTrue(body["selected_workout"]["is_today"])
        self.assertTrue(body["has_workout_today"])
        self.assertIsNone(body["message"])

    def test_workout_landing_returns_closest_upcoming_when_today_missing(self) -> None:
        plan = TrainingPlan.objects.create(name="Summer Block", user_id=str(self.user.id))
        next_workout = Workout.objects.create(
            name="Next Up",
            user_id=str(self.user.id),
            plan=plan,
            date="2026-06-11",
            expected_time=45,
        )
        Workout.objects.create(
            name="Later",
            user_id=str(self.user.id),
            plan=plan,
            date="2026-06-14",
            expected_time=30,
        )

        response = self.client.get(
            reverse("workout-landing"),
            {"today": "2026-06-10"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["selected_workout"]["id"], str(next_workout.id))
        self.assertFalse(body["selected_workout"]["is_today"])
        self.assertFalse(body["has_workout_today"])
        self.assertEqual(body["message"], "No workout scheduled today")

    def test_workout_exercises_page_returns_nested_exercise_display_data(self) -> None:
        workout = Workout.objects.create(name="Upper Body", user_id=str(self.user.id))
        other_workout = Workout.objects.create(name="Other", user_id=str(self.user.id))
        exercise = Exercise.objects.create(name="Bench Press", muscle_group="Chest", user_id=str(self.user.id))
        other_exercise = Exercise.objects.create(name="Row", muscle_group="Back", user_id=str(self.user.id))
        WorkoutExercise.objects.create(workout=workout, exercise=exercise, sets=4, reps=8, weight="135.00")
        WorkoutExercise.objects.create(workout=other_workout, exercise=other_exercise, sets=3, reps=10, weight="95.00")

        response = self.client.get(reverse("workout-exercise-page-collection", args=[workout.id]))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["exercise"]["name"], "Bench Press")
        self.assertEqual(body[0]["exercise"]["muscle_group"], "Chest")
        self.assertEqual(body[0]["exercise"]["prescription_type"], "strength")
        self.assertEqual(body[0]["sets"], 4)

    def test_nested_training_reads_are_scoped_to_authenticated_user(self) -> None:
        User = get_user_model()
        other_user = cast(Any, User.objects).create_user(
            email="other-minimal@example.com",
            password="strong-password",
        )
        other_plan = TrainingPlan.objects.create(name="Theirs", user_id=str(other_user.id))
        other_workout = Workout.objects.create(name="Theirs", user_id=str(other_user.id))

        plan_response = self.client.get(reverse("training-plan-workout-collection", args=[other_plan.id]))
        workout_response = self.client.get(reverse("workout-exercise-page-collection", args=[other_workout.id]))

        self.assertEqual(plan_response.status_code, 404)
        self.assertEqual(workout_response.status_code, 404)
