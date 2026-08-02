from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("training", "0011_remove_planned_workout_requires_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="exercise",
            name="default_weight",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=7,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="exercise",
            name="default_weight_unit",
            field=models.CharField(default="lb", max_length=16),
        ),
    ]
