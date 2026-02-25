import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evidence", "0005_identificationevidence"),
    ]

    operations = [
        migrations.CreateModel(
            name="OtherEvidence",
            fields=[
                (
                    "evidence_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="evidence.evidence",
                    ),
                ),
            ],
            options={
                "verbose_name": "Other Evidence",
                "verbose_name_plural": "Other Evidence",
            },
            bases=("evidence.evidence",),
        ),
    ]
