from django.test import TestCase

from training import services
from training.models import Workout


class WorkoutServiceTests(TestCase):
    user_id = "user-1"

    def test_create_workout(self) -> None:
        starting_count = Workout.objects.count()
        training_plan = services.create_training_plan(
            {"name": "Strength Block"}, user_id=self.user_id
        )
        workout = services.create_workout(
            {
                "plan": str(training_plan.id),
                "name": "Upper Body",
                "date": "2026-06-09",
                "expected_time": 45,
            },
            user_id=self.user_id,
        )
        self.assertEqual(workout.name, "Upper Body")
        self.assertEqual(workout.plan, training_plan)
        self.assertEqual(workout.user_id, self.user_id)
        self.assertEqual(str(workout.date), "2026-06-09")
        self.assertEqual(workout.expected_time, 45)
        self.assertEqual(Workout.objects.count(), starting_count + 1)

    def test_update_workout_expected_time(self) -> None:
        workout = services.create_workout(
            {"name": "Upper Body", "date": "2026-06-09"},
            user_id=self.user_id,
        )
        updated = services.update_workout(
            workout, {"expected_time": 60}, user_id=self.user_id
        )
        self.assertEqual(updated.expected_time, 60)

    def test_workout_requires_date(self) -> None:
        training_plan = services.create_training_plan(
            {"name": "Strength Block"}, user_id=self.user_id
        )

        with self.assertRaises(ValueError):
            services.create_workout(
                {
                    "plan": str(training_plan.id),
                    "name": "Upper Body",
                    "expected_time": 45,
                },
                user_id=self.user_id,
            )

    def test_list_workouts_returns_ascending_dates(self) -> None:
        training_plan = services.create_training_plan(
            {"name": "Strength Block"}, user_id=self.user_id
        )
        services.create_workout(
            {"plan": str(training_plan.id), "name": "Day 3", "date": "2026-06-11"},
            user_id=self.user_id,
        )
        services.create_workout(
            {"plan": str(training_plan.id), "name": "Day 1", "date": "2026-06-09"},
            user_id=self.user_id,
        )
        services.create_workout(
            {"plan": str(training_plan.id), "name": "Day 2", "date": "2026-06-10"},
            user_id=self.user_id,
        )

        workouts = services.list_workouts(self.user_id)

        self.assertEqual(
            [workout.name for workout in workouts],
            ["Day 1", "Day 2", "Day 3"],
        )

    def test_select_workout_landing_prefers_today(self) -> None:
        training_plan = services.create_training_plan(
            {"name": "Strength Block"}, user_id=self.user_id
        )
        services.create_workout(
            {"plan": str(training_plan.id), "name": "Yesterday", "date": "2026-06-09"},
            user_id=self.user_id,
        )
        todays_workout = services.create_workout(
            {"plan": str(training_plan.id), "name": "Today Lift", "date": "2026-06-10"},
            user_id=self.user_id,
        )
        services.create_workout(
            {"plan": str(training_plan.id), "name": "Tomorrow", "date": "2026-06-11"},
            user_id=self.user_id,
        )

        landing = services.get_workout_landing(self.user_id, "2026-06-10")

        assert landing is not None
        self.assertEqual(landing.workout.id, todays_workout.id)
        self.assertTrue(landing.is_today)
        self.assertTrue(landing.has_workout_today)

    def test_select_workout_landing_includes_unplanned_workout_today(self) -> None:
        todays_workout = services.create_workout(
            {"name": "Outdoor Upper Body", "date": "2026-06-10"},
            user_id=self.user_id,
        )

        landing = services.get_workout_landing(self.user_id, "2026-06-10")

        assert landing is not None
        self.assertEqual(landing.workout.id, todays_workout.id)
        self.assertTrue(landing.is_today)
        self.assertTrue(landing.has_workout_today)

    def test_select_workout_landing_uses_closest_upcoming_when_today_missing(
        self,
    ) -> None:
        training_plan = services.create_training_plan(
            {"name": "Strength Block"}, user_id=self.user_id
        )
        services.create_workout(
            {"plan": str(training_plan.id), "name": "Past", "date": "2026-06-09"},
            user_id=self.user_id,
        )
        next_workout = services.create_workout(
            {"plan": str(training_plan.id), "name": "Next Up", "date": "2026-06-11"},
            user_id=self.user_id,
        )
        services.create_workout(
            {"plan": str(training_plan.id), "name": "Later", "date": "2026-06-13"},
            user_id=self.user_id,
        )

        landing = services.get_workout_landing(self.user_id, "2026-06-10")

        assert landing is not None
        self.assertEqual(landing.workout.id, next_workout.id)
        self.assertFalse(landing.is_today)
        self.assertFalse(landing.has_workout_today)
