from django.db import migrations, models
from django.db.models import Q


def merge_duplicate_training_plans(apps, schema_editor):
    TrainingPlan = apps.get_model("training", "TrainingPlan")
    Workout = apps.get_model("training", "Workout")

    duplicate_user_ids = (
        TrainingPlan.objects.exclude(user_id="")
        .values_list("user_id", flat=True)
        .distinct()
    )

    for user_id in duplicate_user_ids:
        plans = list(
            TrainingPlan.objects.filter(user_id=user_id).order_by(
                "created_at",
                "name",
                "id",
            )
        )
        if len(plans) <= 1:
            continue

        keep_plan = plans[0]
        duplicate_ids = [plan.id for plan in plans[1:]]
        Workout.objects.filter(plan_id__in=duplicate_ids).update(plan=keep_plan)
        TrainingPlan.objects.filter(id__in=duplicate_ids).delete()


class Migration(migrations.Migration):
    dependencies = [  # noqa: RUF012
        ("training", "0008_seed_athlete_user"),
    ]

    operations = [  # noqa: RUF012
        migrations.AlterModelOptions(
            name="workout",
            options={"ordering": ["date", "name"]},
        ),
        migrations.RunPython(merge_duplicate_training_plans, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="trainingplan",
            constraint=models.UniqueConstraint(
                condition=~Q(user_id=""),
                fields=("user_id",),
                name="training_plan_one_per_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="workout",
            constraint=models.CheckConstraint(
                condition=Q(plan__isnull=True) | Q(date__isnull=False),
                name="planned_workout_requires_date",
            ),
        ),
    ]
