import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0005_scenecasereport"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("investigation", "0002_suspect_assessment_and_score_history"),
    ]

    operations = [
        migrations.CreateModel(
            name="ArrestOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("issued_at", models.DateTimeField(auto_now_add=True)),
                ("reason", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("executed", "Executed"), ("cancelled", "Cancelled")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="arrest_orders",
                        to="cases.case",
                    ),
                ),
                (
                    "participant",
                    models.ForeignKey(
                        help_text="Case participant with role suspect.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="arrest_orders",
                        to="cases.caseparticipant",
                    ),
                ),
                (
                    "issued_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="arrest_orders_issued",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-issued_at"],
            },
        ),
        migrations.CreateModel(
            name="InterrogationOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ordered_at", models.DateTimeField(auto_now_add=True)),
                ("scheduled_at", models.DateTimeField(blank=True, null=True)),
                ("reason", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("completed", "Completed"), ("cancelled", "Cancelled")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interrogation_orders",
                        to="cases.case",
                    ),
                ),
                (
                    "participant",
                    models.ForeignKey(
                        help_text="Case participant with role suspect.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interrogation_orders",
                        to="cases.caseparticipant",
                    ),
                ),
                (
                    "ordered_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interrogation_orders_issued",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-ordered_at"],
            },
        ),
        migrations.AddIndex(
            model_name="arrestorder",
            index=models.Index(fields=["case"], name="investigati_case_id_arrest_idx"),
        ),
        migrations.AddIndex(
            model_name="arrestorder",
            index=models.Index(fields=["status"], name="investigati_status_arrest_idx"),
        ),
        migrations.AddIndex(
            model_name="interrogationorder",
            index=models.Index(fields=["case"], name="investigati_case_id_interr_idx"),
        ),
        migrations.AddIndex(
            model_name="interrogationorder",
            index=models.Index(fields=["status"], name="investigati_status_interr_idx"),
        ),
    ]
