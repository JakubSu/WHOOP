from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0008_seed_athlete_user"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="workout",
            options={"ordering": ["date", "name"]},
        ),
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
