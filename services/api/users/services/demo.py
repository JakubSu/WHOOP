from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, cast

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from training.models import Exercise, Workout, WorkoutExercise
from training.services.shared_exercise_bank import sync_shared_exercise_bank
from whoop.models import WhoopConnection, WhoopSnapshot

DEMO_WORKOUT_EXERCISES = (
    ("Back Squat", 4, 5, "185.00"),
    ("Deadlift", 3, 5, "225.00"),
    ("Bulgarian Split Squat", 3, 10, "35.00"),
    ("Hamstring Curl", 3, 12, "70.00"),
)


@dataclass(frozen=True, slots=True)
class DemoSession:
    user: Any
    access: str


class CreateDemoSessionService:
    def execute(self) -> DemoSession:
        with transaction.atomic():
            user_model = cast(Any, get_user_model())
            now = timezone.now()
            user = user_model.objects.create_user(
                email=f"demo-{uuid.uuid4()}@demo.invalid",
                password=None,
                display_name="Demo athlete",
                account_type="demo",
                expires_at=now + timedelta(seconds=settings.DEMO_SESSION_TTL_SECONDS),
            )
            user.set_unusable_password()
            user.whoop_user_id = "demo-whoop"
            user.save(update_fields=["password", "whoop_user_id"])
            self._seed_workspace(user=user)
            access = AccessToken.for_user(user)
            access.set_exp(lifetime=timedelta(seconds=settings.DEMO_SESSION_TTL_SECONDS))
            return DemoSession(user=user, access=str(access))

    def _seed_workspace(self, *, user: Any) -> None:
        sync_shared_exercise_bank()
        user_id = str(user.id)
        exercises = {
            exercise.name: exercise
            for exercise in Exercise.objects.filter(
                user_id="", name__in=[item[0] for item in DEMO_WORKOUT_EXERCISES]
            )
        }
        missing = {name for name, *_ in DEMO_WORKOUT_EXERCISES} - set(exercises)
        if missing:
            raise RuntimeError(f"Demo exercise bank is missing: {', '.join(sorted(missing))}.")

        workout = Workout.objects.create(
            user_id=user_id,
            name="Lower Body Strength",
            date=timezone.localdate(user.created_at),
            expected_time=55,
        )
        WorkoutExercise.objects.bulk_create(
            [
                WorkoutExercise(
                    workout=workout,
                    exercise=exercises[name],
                    sets=sets,
                    reps=reps,
                    weight=weight,
                    weight_unit="lb",
                    sort_order=index,
                )
                for index, (name, sets, reps, weight) in enumerate(DEMO_WORKOUT_EXERCISES)
            ]
        )
        snapshot = WhoopSnapshot.objects.create(
            user_id=user_id,
            snapshot_date=timezone.localdate(user.created_at),
            recovery_score="78.00",
            sleep_performance_percent="88.00",
            day_strain="7.40",
            hrv_rmssd_milli="52.00",
            resting_heart_rate="56.00",
            sleep_duration_minutes=442,
            recent_workout_count=1,
            raw_payload={"recent_workouts": []},
        )
        WhoopSnapshot.objects.filter(pk=snapshot.pk).update(created_at=user.created_at)
        WhoopConnection.objects.create(
            user_id=user_id,
            whoop_user_id=user.whoop_user_id,
            access_token_encrypted="demo",
            refresh_token_encrypted="",
            expires_at=user.expires_at,
            scopes="demo",
        )
