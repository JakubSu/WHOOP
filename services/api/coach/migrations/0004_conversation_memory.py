import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("coaching", "0003_uiaction")]

    operations = [
        migrations.AddField(
            model_name="coachconversation",
            name="memory",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="coachconversation",
            name="memory_through_message",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="coaching.coachmessage",
            ),
        ),
    ]
