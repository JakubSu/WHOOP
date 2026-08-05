import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coaching", "0001_initial"),
        ("recommendation", "0008_align_operation_ledger"),
    ]

    operations = [
        migrations.AlterField(
            model_name="recommendation",
            name="conversation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="recommendations",
                to="coaching.coachconversation",
            ),
        ),
    ]
