import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("cases", "0005_scenecasereport"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Evidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("evidence_type", models.CharField(db_index=True, max_length=30, choices=[
                    ("witness_testimony", "Witness / Local Testimony"),
                    ("biological_medical", "Found: Biological / Medical"),
                    ("vehicle", "Found: Vehicle"),
                    ("identification", "Found: Identification Document"),
                    ("other", "Other Evidence"),
                ])),
                ("registered_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evidence_items",
                        to="cases.case",
                    ),
                ),
                (
                    "registrar",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="evidence_registered",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Evidence",
                "verbose_name_plural": "Evidence",
                "ordering": ["-registered_at", "-created_at"],
                "indexes": [
                    models.Index(fields=["case", "evidence_type"], name="evidence_ev_case_id_9f9eb0_idx"),
                    models.Index(fields=["registered_at"], name="evidence_ev_registe_3c8da3_idx"),
                ],
            },
        ),
    ]
