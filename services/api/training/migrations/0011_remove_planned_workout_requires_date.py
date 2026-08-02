from datetime import date

from django.db import migrations, models


def fill_missing_workout_dates(apps, schema_editor):
    Workout = apps.get_model("training", "Workout")
    for workout in Workout.objects.filter(date__isnull=True).only("id", "created_at"):
        workout.date = workout.created_at.date() if workout.created_at else date(1970, 1, 1)
        workout.save(update_fields=["date"])


class Migration(migrations.Migration):

    dependencies = [  # noqa: RUF012
        ("training", "0010_workoutexercise_sort_order"),
    ]

    operations = [  # noqa: RUF012
        migrations.RemoveConstraint(
            model_name="workout",
            name="planned_workout_requires_date",
        ),
        migrations.RunPython(fill_missing_workout_dates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="workout",
            name="date",
            field=models.DateField(),
        ),
    ]
