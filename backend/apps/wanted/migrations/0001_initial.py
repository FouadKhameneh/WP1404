import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("cases", "0005_scenecasereport"),
    ]

    operations = [
        migrations.CreateModel(
            name="Wanted",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("marked_at", models.DateTimeField(default=timezone.now)),
                (
                    "status",
                    models.CharField(
                        choices=[("wanted", "Wanted"), ("most_wanted", "Most Wanted")],
                        default="wanted",
                        max_length=20,
                    ),
                ),
                ("promoted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wanted_entries",
                        to="cases.case",
                    ),
                ),
                (
                    "participant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wanted_entries",
                        to="cases.caseparticipant",
                    ),
                ),
            ],
            options={
                "ordering": ["-marked_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="wanted",
            constraint=models.UniqueConstraint(
                fields=("case", "participant"),
                name="wanted_unique_case_participant",
            ),
        ),
        migrations.AddIndex(
            model_name="wanted",
            index=models.Index(fields=["status"], name="wanted_wanted_status_idx"),
        ),
        migrations.AddIndex(
            model_name="wanted",
            index=models.Index(fields=["marked_at"], name="wanted_wanted_marked_at_idx"),
        ),
    ]
