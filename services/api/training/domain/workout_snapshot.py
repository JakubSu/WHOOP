from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _as_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _date_to_str(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _datetime_to_str(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()


def _decimal_to_str(value: Decimal | str | int | float) -> str:
    if isinstance(value, Decimal):
        return str(value)
    return str(Decimal(str(value)))


@dataclass(frozen=True)
class ExerciseSummary:
    id: str
    name: str
    category: str
    primary_muscle_group: str = ""
    secondary_muscle_groups: list[str] = field(default_factory=list)
    equipment: str = ""
    default_intensity: str = ""
    is_favorite: bool = False
    is_avoided: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "primary_muscle_group": self.primary_muscle_group,
            "secondary_muscle_groups": self.secondary_muscle_groups,
            "equipment": self.equipment,
            "default_intensity": self.default_intensity,
            "is_favorite": self.is_favorite,
            "is_avoided": self.is_avoided,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExerciseSummary:
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            category=str(data["category"]),
            primary_muscle_group=str(data.get("primary_muscle_group", "")),
            secondary_muscle_groups=list(data.get("secondary_muscle_groups", [])),
            equipment=str(data.get("equipment", "")),
            default_intensity=str(data.get("default_intensity", "")),
            is_favorite=bool(data.get("is_favorite", False)),
            is_avoided=bool(data.get("is_avoided", False)),
            notes=str(data.get("notes", "")),
        )


@dataclass(frozen=True)
class WorkoutSnapshotExercise:
    workout_exercise_id: str | None
    snapshot_exercise_key: str
    exercise: ExerciseSummary
    position: int = 1
    sets: int = 0
    reps: int = 0
    duration_seconds: int = 0
    distance: Decimal | str = Decimal("0.00")
    load: Decimal | str = Decimal("0.00")
    intensity: str = ""
    rest_seconds: int = 0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "workout_exercise_id": self.workout_exercise_id,
            "snapshot_exercise_key": self.snapshot_exercise_key,
            "exercise": self.exercise.to_dict(),
            "position": self.position,
            "sets": self.sets,
            "reps": self.reps,
            "duration_seconds": self.duration_seconds,
            "distance": _decimal_to_str(self.distance),
            "load": _decimal_to_str(self.load),
            "intensity": self.intensity,
            "rest_seconds": self.rest_seconds,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkoutSnapshotExercise:
        workout_exercise_id = _as_str(data.get("workout_exercise_id"))
        snapshot_exercise_key = data.get("snapshot_exercise_key") or workout_exercise_id
        if not snapshot_exercise_key:
            raise ValueError("snapshot_exercise_key is required when workout_exercise_id is missing.")

        return cls(
            workout_exercise_id=workout_exercise_id,
            snapshot_exercise_key=str(snapshot_exercise_key),
            exercise=ExerciseSummary.from_dict(data["exercise"]),
            position=int(data.get("position", 1)),
            sets=int(data.get("sets", 0)),
            reps=int(data.get("reps", 0)),
            duration_seconds=int(data.get("duration_seconds", 0)),
            distance=Decimal(str(data.get("distance", "0.00"))),
            load=Decimal(str(data.get("load", "0.00"))),
            intensity=str(data.get("intensity", "")),
            rest_seconds=int(data.get("rest_seconds", 0)),
            notes=str(data.get("notes", "")),
        )

    def identity(self) -> tuple[str, str]:
        if self.workout_exercise_id:
            return ("workout_exercise_id", self.workout_exercise_id)
        return ("snapshot_exercise_key", self.snapshot_exercise_key)

    def prescription_dict(self) -> dict[str, Any]:
        data = self.to_dict()
        data["exercise_id"] = self.exercise.id
        data.pop("exercise")
        data.pop("position")
        return data


@dataclass(frozen=True)
class WorkoutSnapshot:
    id: str | None
    user_id: str | None
    version: str | None
    training_plan: str | None
    scheduled_date: date | str | None
    name: str
    workout_type: str
    status: str
    planned_intensity: str = ""
    planned_duration_minutes: int = 0
    completed_at: datetime | str | None = None
    actual_strain: Decimal | str = Decimal("0.00")
    notes: str = ""
    exercises: list[WorkoutSnapshotExercise] = field(default_factory=list)
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "version": self.version,
            "training_plan": self.training_plan,
            "scheduled_date": self.scheduled_date if isinstance(self.scheduled_date, str) else _date_to_str(self.scheduled_date),
            "name": self.name,
            "workout_type": self.workout_type,
            "status": self.status,
            "planned_intensity": self.planned_intensity,
            "planned_duration_minutes": self.planned_duration_minutes,
            "completed_at": _datetime_to_str(self.completed_at),
            "actual_strain": _decimal_to_str(self.actual_strain),
            "notes": self.notes,
            "exercises": [exercise.to_dict() for exercise in self.exercises],
            "created_at": _datetime_to_str(self.created_at),
            "updated_at": _datetime_to_str(self.updated_at),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkoutSnapshot:
        return cls(
            id=_as_str(data.get("id")),
            user_id=_as_str(data.get("user_id")),
            version=_as_str(data.get("version")),
            training_plan=_as_str(data.get("training_plan")),
            scheduled_date=data.get("scheduled_date"),
            name=str(data["name"]),
            workout_type=str(data["workout_type"]),
            status=str(data["status"]),
            planned_intensity=str(data.get("planned_intensity", "")),
            planned_duration_minutes=int(data.get("planned_duration_minutes", 0)),
            completed_at=data.get("completed_at"),
            actual_strain=Decimal(str(data.get("actual_strain", "0.00"))),
            notes=str(data.get("notes", "")),
            exercises=[
                WorkoutSnapshotExercise.from_dict(exercise)
                for exercise in data.get("exercises", [])
            ],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_llm_context(self) -> dict[str, Any]:
        return {
            "workout": {
                "id": self.id,
                "scheduled_date": self.scheduled_date if isinstance(self.scheduled_date, str) else _date_to_str(self.scheduled_date),
                "name": self.name,
                "workout_type": self.workout_type,
                "status": self.status,
                "planned_intensity": self.planned_intensity,
                "planned_duration_minutes": self.planned_duration_minutes,
                "actual_strain": _decimal_to_str(self.actual_strain),
                "notes": self.notes,
            },
            "exercises": [
                {
                    "snapshot_exercise_key": exercise.snapshot_exercise_key,
                    "name": exercise.exercise.name,
                    "category": exercise.exercise.category,
                    "primary_muscle_group": exercise.exercise.primary_muscle_group,
                    "secondary_muscle_groups": exercise.exercise.secondary_muscle_groups,
                    "equipment": exercise.exercise.equipment,
                    "default_intensity": exercise.exercise.default_intensity,
                    "is_favorite": exercise.exercise.is_favorite,
                    "is_avoided": exercise.exercise.is_avoided,
                    "position": exercise.position,
                    "sets": exercise.sets,
                    "reps": exercise.reps,
                    "duration_seconds": exercise.duration_seconds,
                    "distance": _decimal_to_str(exercise.distance),
                    "load": _decimal_to_str(exercise.load),
                    "intensity": exercise.intensity,
                    "rest_seconds": exercise.rest_seconds,
                    "notes": exercise.notes,
                }
                for exercise in self.exercises
            ],
        }


@dataclass(frozen=True)
class WorkoutDiff:
    workout_changes: dict[str, dict[str, Any]] = field(default_factory=dict)
    added_exercises: list[dict[str, Any]] = field(default_factory=list)
    removed_exercises: list[dict[str, Any]] = field(default_factory=list)
    modified_exercises: list[dict[str, Any]] = field(default_factory=list)
    reordered_exercises: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workout_changes": self.workout_changes,
            "added_exercises": self.added_exercises,
            "removed_exercises": self.removed_exercises,
            "modified_exercises": self.modified_exercises,
            "reordered_exercises": self.reordered_exercises,
        }


class WorkoutSnapshotDiffer:
    workout_fields = (
        "training_plan",
        "scheduled_date",
        "name",
        "workout_type",
        "status",
        "planned_intensity",
        "planned_duration_minutes",
        "completed_at",
        "actual_strain",
        "notes",
    )
    exercise_fields = (
        "exercise_id",
        "sets",
        "reps",
        "duration_seconds",
        "distance",
        "load",
        "intensity",
        "rest_seconds",
        "notes",
    )

    @classmethod
    def compare(cls, before: WorkoutSnapshot, after: WorkoutSnapshot) -> WorkoutDiff:
        before_data = before.to_dict()
        after_data = after.to_dict()
        workout_changes = {
            field: {"before": before_data[field], "after": after_data[field]}
            for field in cls.workout_fields
            if before_data[field] != after_data[field]
        }

        before_by_identity = {
            exercise.identity(): exercise for exercise in before.exercises
        }
        after_by_identity = {
            exercise.identity(): exercise for exercise in after.exercises
        }

        added = [
            exercise.to_dict()
            for identity, exercise in after_by_identity.items()
            if identity not in before_by_identity
        ]
        removed = [
            exercise.to_dict()
            for identity, exercise in before_by_identity.items()
            if identity not in after_by_identity
        ]

        modified: list[dict[str, Any]] = []
        reordered: list[dict[str, Any]] = []
        for identity, before_exercise in before_by_identity.items():
            after_exercise = after_by_identity.get(identity)
            if after_exercise is None:
                continue

            field_changes = cls._exercise_field_changes(before_exercise, after_exercise)
            if field_changes:
                modified.append(
                    {
                        "identity": cls._identity_to_dict(identity),
                        "snapshot_exercise_key": after_exercise.snapshot_exercise_key,
                        "exercise_name": after_exercise.exercise.name,
                        "changes": field_changes,
                    }
                )

            if before_exercise.position != after_exercise.position:
                reordered.append(
                    {
                        "identity": cls._identity_to_dict(identity),
                        "snapshot_exercise_key": after_exercise.snapshot_exercise_key,
                        "exercise_name": after_exercise.exercise.name,
                        "before": before_exercise.position,
                        "after": after_exercise.position,
                    }
                )

        return WorkoutDiff(
            workout_changes=workout_changes,
            added_exercises=added,
            removed_exercises=removed,
            modified_exercises=modified,
            reordered_exercises=reordered,
        )

    @classmethod
    def _exercise_field_changes(
        cls,
        before: WorkoutSnapshotExercise,
        after: WorkoutSnapshotExercise,
    ) -> dict[str, dict[str, Any]]:
        before_data = before.prescription_dict()
        after_data = after.prescription_dict()
        return {
            field: {"before": before_data[field], "after": after_data[field]}
            for field in cls.exercise_fields
            if before_data[field] != after_data[field]
        }

    @staticmethod
    def _identity_to_dict(identity: tuple[str, str]) -> dict[str, str]:
        return {"type": identity[0], "value": identity[1]}
