import json
import uuid
from decimal import Decimal
from pathlib import Path

from django.db import migrations, models
import django.db.models.deletion


def seed_exercise_bank(apps, schema_editor):
    Exercise = apps.get_model("training", "Exercise")
    data_path = Path(__file__).resolve().parent.parent / "data" / "exercise_bank.json"
    records = json.loads(data_path.read_text(encoding="utf-8"))

    for record in records:
        Exercise.objects.update_or_create(
            user_id=record["user_id"],
            name=record["name"],
            defaults={
                "category": record["category"],
                "primary_muscle_group": record["primary_muscle_group"],
                "equipment": record["equipment"],
                "notes": record["notes"],
                "default_sets": record["default_sets"],
                "default_reps": record["default_reps"],
                "is_favorite": record["is_favorite"],
                "is_avoided": record["is_avoided"],
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0002_workout"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrainingPlan",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user_id", models.CharField(blank=True, default="", max_length=200)),
                ("name", models.CharField(max_length=200)),
                ("goal", models.CharField(blank=True, default="", max_length=200)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("active", "Active"),
                            ("paused", "Paused"),
                            ("completed", "Completed"),
                            ("archived", "Archived"),
                        ],
                        default="draft",
                        max_length=32,
                    ),
                ),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at", "name"],
            },
        ),
        migrations.RenameField(
            model_name="workout",
            old_name="training_plan_id",
            new_name="training_plan",
        ),
        migrations.AlterField(
            model_name="workout",
            name="training_plan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="workouts",
                to="training.trainingplan",
            ),
        ),
        migrations.CreateModel(
            name="WorkoutExercise",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("position", models.PositiveIntegerField(default=1)),
                ("sets", models.PositiveIntegerField(default=0)),
                ("reps", models.PositiveIntegerField(default=0)),
                ("duration_seconds", models.PositiveIntegerField(default=0)),
                ("load", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=7)),
                ("rest_seconds", models.PositiveIntegerField(default=0)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "exercise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="workout_exercises",
                        to="training.exercise",
                    ),
                ),
                (
                    "workout",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workout_exercises",
                        to="training.workout",
                    ),
                ),
            ],
            options={
                "ordering": ["workout", "position"],
            },
        ),
        migrations.AddConstraint(
            model_name="workoutexercise",
            constraint=models.UniqueConstraint(
                fields=("workout", "position"),
                name="unique_workout_exercise_position",
            ),
        ),
        migrations.RunPython(seed_exercise_bank, migrations.RunPython.noop),
    ]
