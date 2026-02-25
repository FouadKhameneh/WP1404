import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evidence", "0004_vehicleevidence"),
    ]

    operations = [
        migrations.CreateModel(
            name="IdentificationEvidence",
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
                (
                    "attributes",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Key-value document attributes (e.g. full_name, national_id). Keys: strings; values: primitives.",
                    ),
                ),
                (
                    "attributes_schema",
                    models.JSONField(
                        blank=True,
                        help_text="Optional schema: {key: type}. Types: string, integer, number, boolean, null. When set, validates attributes.",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Identification Document Evidence",
                "verbose_name_plural": "Identification Document Evidence",
            },
            bases=("evidence.evidence",),
        ),
    ]
