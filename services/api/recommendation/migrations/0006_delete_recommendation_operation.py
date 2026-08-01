# ruff: noqa: RUF012

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("recommendation", "0005_domain_operation_on_recommendation"),
    ]

    operations = [
        migrations.DeleteModel(
            name="RecommendationOperation",
        ),
    ]
