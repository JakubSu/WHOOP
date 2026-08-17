from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("coaching", "0003_uiaction")]

    operations = [
        migrations.AddField(
            model_name="coachmessage",
            name="view_context",
            field=models.JSONField(blank=True, null=True),
        )
    ]
