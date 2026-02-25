import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("evidence", "0003_biologicalmedicalevidence_biologicalmedicalmediareference"),
    ]

    operations = [
        migrations.CreateModel(
            name="VehicleEvidence",
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
                ("model", models.CharField(max_length=100)),
                ("color", models.CharField(max_length=50)),
                ("plate", models.CharField(blank=True, help_text="Required if vehicle has plate; mutually exclusive with serial_number", max_length=20)),
                (
                    "serial_number",
                    models.CharField(
                        blank=True,
                        help_text="Required if vehicle has no plate; mutually exclusive with plate",
                        max_length=100,
                    ),
                ),
            ],
            options={
                "verbose_name": "Vehicle Evidence",
                "verbose_name_plural": "Vehicle Evidence",
                "constraints": [
                    models.CheckConstraint(
                        condition=(Q(plate__gt="") & Q(serial_number="")) | (Q(plate="") & Q(serial_number__gt="")),
                        name="evidence_vehicle_plate_xor_serial",
                    ),
                ],
            },
            bases=("evidence.evidence",),
        ),
    ]
