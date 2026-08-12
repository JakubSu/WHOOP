from django.db import migrations, models

CANONICAL_GROUPS = {
    "chest": "chest",
    "back": "back",
    "shoulders": "shoulders",
    "biceps": "biceps",
    "triceps": "triceps",
    "forearms": "forearms",
    "quads": "quads",
    "hamstrings": "hamstrings",
    "glutes": "glutes",
    "calves": "calves",
    "core": "core",
    "full body": "full_body",
    "full_body": "full_body",
}


def normalize_muscle_groups(apps, schema_editor):
    """Maps legacy free-text values to the canonical enum or its safe fallback."""

    Exercise = apps.get_model("training", "Exercise")
    for exercise in Exercise.objects.only("id", "muscle_group").iterator():
        normalized = CANONICAL_GROUPS.get(
            exercise.muscle_group.strip().lower(), "other"
        )
        if exercise.muscle_group != normalized:
            Exercise.objects.filter(pk=exercise.pk).update(muscle_group=normalized)


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0012_exercise_default_weight"),
    ]

    operations = [
        migrations.RunPython(normalize_muscle_groups, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="exercise",
            name="muscle_group",
            field=models.CharField(
                choices=[
                    ("chest", "Chest"),
                    ("back", "Back"),
                    ("shoulders", "Shoulders"),
                    ("biceps", "Biceps"),
                    ("triceps", "Triceps"),
                    ("forearms", "Forearms"),
                    ("quads", "Quads"),
                    ("hamstrings", "Hamstrings"),
                    ("glutes", "Glutes"),
                    ("calves", "Calves"),
                    ("core", "Core"),
                    ("full_body", "Full body"),
                    ("other", "Other"),
                ],
                default="other",
                max_length=16,
            ),
        ),
        migrations.AddConstraint(
            model_name="exercise",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    muscle_group__in=[
                        "chest",
                        "back",
                        "shoulders",
                        "biceps",
                        "triceps",
                        "forearms",
                        "quads",
                        "hamstrings",
                        "glutes",
                        "calves",
                        "core",
                        "full_body",
                        "other",
                    ]
                ),
                name="exercise_muscle_group_valid",
            ),
        ),
    ]
