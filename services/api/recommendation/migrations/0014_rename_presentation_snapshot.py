from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("recommendation", "0013_move_source_to_recommendation")]

    operations = [
        migrations.RenameField(
            model_name="recommendation",
            old_name="presentation_snapshot",
            new_name="coach_card_snapshot",
        )
    ]
