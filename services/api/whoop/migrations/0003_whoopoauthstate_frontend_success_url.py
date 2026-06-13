from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("whoop", "0002_whoopoauthstate"),
    ]

    operations = [
        migrations.AddField(
            model_name="whoopoauthstate",
            name="frontend_success_url",
            field=models.URLField(blank=True, default="", max_length=2048),
        ),
    ]
