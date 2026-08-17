"""Synchronization of the version-controlled shared exercise library."""

import json
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction

from training.models import Exercise


@dataclass(frozen=True, slots=True)
class SharedExerciseBankSyncResult:
    created: int = 0
    updated: int = 0
    unchanged: int = 0


def sync_shared_exercise_bank() -> SharedExerciseBankSyncResult:
    """Create or update shared exercises from the committed JSON exercise bank.

    The operation deliberately never removes records. Removing a shared exercise can
    invalidate existing workout prescriptions, so that needs an explicit workflow.
    """

    records = _load_shared_exercise_bank()
    created = updated = unchanged = 0

    with transaction.atomic():
        for record in records:
            defaults = _exercise_defaults(record)
            exercise, was_created = Exercise.objects.get_or_create(
                user_id="", name=record["name"], defaults=defaults
            )
            if was_created:
                created += 1
                continue

            changed_fields = [
                field
                for field, value in defaults.items()
                if getattr(exercise, field) != value
            ]
            if not changed_fields:
                unchanged += 1
                continue

            for field in changed_fields:
                setattr(exercise, field, defaults[field])
            exercise.save(update_fields=[*changed_fields, "updated_at"])
            updated += 1

    return SharedExerciseBankSyncResult(created, updated, unchanged)


def _load_shared_exercise_bank() -> list[dict[str, object]]:
    data_path = Path(__file__).resolve().parent.parent / "data" / "shared_exercise_bank.json"
    return json.loads(data_path.read_text(encoding="utf-8"))


def _exercise_defaults(record: dict[str, object]) -> dict[str, object]:
    return {
        "prescription_type": record["prescription_type"],
        "default_sets": record["default_sets"],
        "default_reps": record["default_reps"],
        "default_weight": record.get("default_weight"),
        "default_weight_unit": record.get("default_weight_unit", "lb"),
        "muscle_group": record["muscle_group"],
        "default_time": record["default_time"],
        "notes": record.get("notes", ""),
    }
