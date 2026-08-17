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
            {
                "name": "Upper Body",
                "date": "2026-06-09",
                "user_id": str(self.other_user.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        workout = Workout.objects.get(name="Upper Body", user_id=str(self.user.id))
        self.assertEqual(workout.user_id, str(self.user.id))
        self.assertNotIn("user_id", response.json())

    def test_workout_list_is_scoped_to_authenticated_user(self) -> None:
        Workout.objects.create(
            name="Mine", date="2026-06-09", user_id=str(self.user.id)
        )
        Workout.objects.create(
            name="Theirs", date="2026-06-09", user_id=str(self.other_user.id)
        )

        response = self.client.get(reverse("workout-collection"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "Mine")

    def test_detail_does_not_return_other_user_workout(self) -> None:
        workout = Workout.objects.create(
            name="Theirs",
            date="2026-06-09",
            user_id=str(self.other_user.id),
        )

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

    def test_create_minimal_training_flow_uses_spec_routes(self) -> None:
        workout_response = self.client.post(
            reverse("workout-collection"),
            {
                "name": "Upper Body",
                "date": "2026-06-09",
                "expected_time": 45,
            },
            format="json",
        )
        self.assertEqual(workout_response.status_code, 201)
        self.assertEqual(
            set(workout_response.json().keys()),
            {"id", "name", "date", "expected_time", "exercise_count"},
        )

        exercise_response = self.client.post(
            reverse("exercise-collection"),
            {
                "name": "Bench Press",
                "default_sets": 4,
                "default_reps": 8,
                "default_weight": "135.00",
                "default_weight_unit": "lb",
                "muscle_group": "chest",
                "default_time": 0,
                "notes": "Pause reps.",
            },
            format="json",
        )
        self.assertEqual(exercise_response.status_code, 201)
        self.assertEqual(exercise_response.json()["default_weight"], "135.00")
        self.assertEqual(exercise_response.json()["default_weight_unit"], "lb")

        workout_exercise_response = self.client.post(
            reverse(
                "workout-exercise-page-collection", args=[workout_response.json()["id"]]
            ),
            {
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
            {
                "id",
                "workout",
                "exercise",
                "sets",
                "reps",
                "time",
                "sort_order",
                "weight",
                "weight_unit",
                "note",
            },
        )

    def test_exercise_list_filters_by_a_valid_muscle_group(self) -> None:
        """The exercise API validates and applies the canonical muscle-group filter."""

        chest = Exercise.objects.create(
            name="Bench Press",
            user_id=str(self.user.id),
            muscle_group=Exercise.MuscleGroup.CHEST,
        )
        Exercise.objects.create(
            name="Barbell Row",
            user_id=str(self.user.id),
            muscle_group=Exercise.MuscleGroup.BACK,
        )

        response = self.client.get(
            reverse("exercise-collection"), {"muscleGroup": "chest"}
        )
        invalid_response = self.client.get(
            reverse("exercise-collection"), {"muscleGroup": "legs"}
        )
        invalid_create_response = self.client.post(
            reverse("exercise-collection"),
            {"name": "Invalid exercise", "muscle_group": "legs"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(str(chest.id), [item["id"] for item in response.json()])
        self.assertTrue(
            all(item["muscle_group"] == "chest" for item in response.json())
        )
        self.assertEqual(invalid_response.status_code, 400)
        self.assertEqual(invalid_create_response.status_code, 400)

    def test_patch_nested_workout_exercise_minimal_fields(self) -> None:
        workout = Workout.objects.create(
            name="Upper Body",
            date="2026-06-09",
            user_id=str(self.user.id),
        )
        exercise = Exercise.objects.create(
            name="Bench Press", user_id=str(self.user.id)
        )
        workout_exercise = WorkoutExercise.objects.create(
            workout=workout, exercise=exercise
        )

        response = self.client.patch(
            reverse(
                "workout-exercise-page-detail", args=[workout.id, workout_exercise.id]
            ),
            {
                "sets": 5,
                "reps": 6,
                "weight": "155.50",
                "weight_unit": "lb",
                "note": "Top set.",
            },
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
        workout = Workout.objects.create(
            name="Upper Body",
            date="2026-06-09",
            user_id=str(self.user.id),
        )
        exercise = Exercise.objects.create(
            name="Bench Press", user_id=str(self.user.id)
        )

        response = self.client.post(
            reverse("workout-exercise-page-collection", args=[workout.id]),
            {
                "exercise": str(exercise.id),
                "sets": 4,
                "reps": 8,
                "time": 20,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_timed_workout_exercise_accepts_time(self) -> None:
        workout = Workout.objects.create(
            name="Core",
            date="2026-06-09",
            user_id=str(self.user.id),
        )
        exercise = Exercise.objects.create(
            name="Plank",
            prescription_type=Exercise.PrescriptionType.TIMED_SETS,
            user_id=str(self.user.id),
        )

        response = self.client.post(
            reverse("workout-exercise-page-collection", args=[workout.id]),
            {
                "exercise": str(exercise.id),
                "time": 45,
                "weight": "10.00",
                "weight_unit": "kg",
                "note": "Brace.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["time"], 45)
        self.assertEqual(response.json()["weight"], "10.00")
        self.assertEqual(response.json()["weight_unit"], "kg")

    def test_workout_list_returns_exercise_count_and_date(self) -> None:
        workout = Workout.objects.create(
            name="Upper Body",
            user_id=str(self.user.id),
            date="2026-06-10",
            expected_time=45,
        )
        exercise_one = Exercise.objects.create(
            name="Bench Press", user_id=str(self.user.id)
        )
        exercise_two = Exercise.objects.create(name="Row", user_id=str(self.user.id))
        WorkoutExercise.objects.create(workout=workout, exercise=exercise_one)
        WorkoutExercise.objects.create(workout=workout, exercise=exercise_two)

        response = self.client.get(reverse("workout-collection"))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["id"], str(workout.id))
        self.assertEqual(body["results"][0]["date"], "2026-06-10")
        self.assertEqual(body["results"][0]["exercise_count"], 2)
        self.assertNotIn("status", body["results"][0])

    def test_workout_list_supports_date_window_and_pagination(self) -> None:
        Workout.objects.create(
            name="Before",
            user_id=str(self.user.id),
            date="2026-06-08",
        )
        Workout.objects.create(
            name="First",
            user_id=str(self.user.id),
            date="2026-06-09",
        )
        second = Workout.objects.create(
            name="Second",
            user_id=str(self.user.id),
            date="2026-06-10",
        )
        Workout.objects.create(
            name="Third",
            user_id=str(self.user.id),
            date="2026-06-11",
        )
        Workout.objects.create(
            name="After",
            user_id=str(self.user.id),
            date="2026-06-12",
        )

        response = self.client.get(
            reverse("workout-collection"),
            {
                "startDate": "2026-06-09",
                "endDate": "2026-06-11",
                "page": 2,
                "pageSize": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 3)
        self.assertEqual(body["page"], 2)
        self.assertEqual(body["page_size"], 1)
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["id"], str(second.id))

    def test_workout_list_rejects_invalid_date_window(self) -> None:
        response = self.client.get(
            reverse("workout-collection"),
            {
                "startDate": "2026-06-12",
                "endDate": "2026-06-09",
                "page": 1,
                "pageSize": 20,
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_workout_list_uses_default_page_size_and_accepts_override(self) -> None:
        for index in range(55):
            Workout.objects.create(
                name=f"Workout {index:02d}",
                user_id=str(self.user.id),
                date="2026-06-10",
            )

        default_response = self.client.get(reverse("workout-collection"))
        override_response = self.client.get(
            reverse("workout-collection"),
            {"pageSize": 10},
        )

        self.assertEqual(default_response.status_code, 200)
        default_body = default_response.json()
        self.assertEqual(default_body["count"], 55)
        self.assertEqual(default_body["page_size"], 50)
        self.assertEqual(len(default_body["results"]), 50)

        self.assertEqual(override_response.status_code, 200)
        override_body = override_response.json()
        self.assertEqual(override_body["count"], 55)
        self.assertEqual(override_body["page_size"], 10)
        self.assertEqual(len(override_body["results"]), 10)

    def test_workout_landing_returns_todays_workout(self) -> None:
        plan = TrainingPlan.objects.create(
            name="Summer Block", user_id=str(self.user.id)
        )
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
        plan = TrainingPlan.objects.create(
            name="Summer Block", user_id=str(self.user.id)
        )
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
        workout = Workout.objects.create(
            name="Upper Body",
            date="2026-06-09",
            user_id=str(self.user.id),
        )
        other_workout = Workout.objects.create(
            name="Other",
            date="2026-06-10",
            user_id=str(self.user.id),
        )
        exercise = Exercise.objects.create(
            name="Bench Press", muscle_group="chest", user_id=str(self.user.id)
        )
        other_exercise = Exercise.objects.create(
            name="Row", muscle_group="back", user_id=str(self.user.id)
        )
        WorkoutExercise.objects.create(
            workout=workout, exercise=exercise, sets=4, reps=8, weight="135.00"
        )
        WorkoutExercise.objects.create(
            workout=other_workout,
            exercise=other_exercise,
            sets=3,
            reps=10,
            weight="95.00",
        )

        response = self.client.get(
            reverse("workout-exercise-page-collection", args=[workout.id])
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["exercise"]["name"], "Bench Press")
        self.assertEqual(body[0]["exercise"]["muscle_group"], "chest")
        self.assertEqual(body[0]["exercise"]["prescription_type"], "strength")
        self.assertEqual(body[0]["sets"], 4)

    def test_nested_training_reads_are_scoped_to_authenticated_user(self) -> None:
        User = get_user_model()
        other_user = cast(Any, User.objects).create_user(
            email="other-minimal@example.com",
            password="strong-password",
        )
        other_workout = Workout.objects.create(
            name="Theirs",
            date="2026-06-09",
            user_id=str(other_user.id),
        )

        workout_response = self.client.get(
            reverse("workout-exercise-page-collection", args=[other_workout.id])
        )

        self.assertEqual(workout_response.status_code, 404)
