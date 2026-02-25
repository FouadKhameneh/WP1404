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
            name="CaseVerdict",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "verdict",
                    models.CharField(
                        choices=[("guilty", "Guilty"), ("not_guilty", "Not Guilty")],
                        max_length=20,
                    ),
                ),
                ("punishment_title", models.CharField(blank=True, max_length=200)),
                ("punishment_description", models.TextField(blank=True)),
                ("recorded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "case",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="verdict",
                        to="cases.case",
                    ),
                ),
                (
                    "judge",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="case_verdicts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Case Verdict",
                "verbose_name_plural": "Case Verdicts",
            },
        ),
        migrations.AddIndex(
            model_name="caseverdict",
            index=models.Index(fields=["verdict"], name="judiciary_c_verdict_idx"),
        ),
    ]
