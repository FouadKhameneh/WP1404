import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evidence", "0002_witnesstestimony_witnesstestimonyattachment"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BiologicalMedicalEvidence",
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
                    "coroner_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending Coroner Review"),
                            ("submitted", "Submitted to Coroner"),
                            ("result_received", "Result Received"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("coroner_result", models.TextField(blank=True, help_text="Coroner or database review result (filled when received)")),
                ("result_submitted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "coroner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="biological_medical_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Biological / Medical Evidence",
                "verbose_name_plural": "Biological / Medical Evidence",
            },
            bases=("evidence.evidence",),
        ),
        migrations.CreateModel(
            name="BiologicalMedicalMediaReference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="evidence/biological_medical/")),
                (
                    "media_type",
                    models.CharField(
                        choices=[("image", "Image"), ("video", "Video")],
                        db_index=True,
                        default="image",
                        max_length=10,
                    ),
                ),
                ("width", models.PositiveIntegerField(blank=True, null=True)),
                ("height", models.PositiveIntegerField(blank=True, null=True)),
                ("file_size", models.PositiveBigIntegerField(blank=True, null=True)),
                ("mime_type", models.CharField(blank=True, max_length=100)),
                ("caption", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "biological_medical_evidence",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="media_references",
                        to="evidence.biologicalmedicalevidence",
                    ),
                ),
            ],
            options={
                "verbose_name": "Biological/Medical Media Reference",
                "verbose_name_plural": "Biological/Medical Media References",
                "ordering": ["created_at"],
            },
        ),
    ]
