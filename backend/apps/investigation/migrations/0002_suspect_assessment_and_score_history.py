import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0005_scenecasereport"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("investigation", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SuspectAssessment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suspect_assessments",
                        to="cases.case",
                    ),
                ),
                (
                    "participant",
                    models.ForeignKey(
                        help_text="Case participant with role suspect.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suspect_assessments",
                        to="cases.caseparticipant",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SuspectAssessmentScoreEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "role_key",
                    models.CharField(
                        choices=[("detective", "Detective"), ("sergeant", "Sergeant")],
                        max_length=20,
                    ),
                ),
                ("score", models.PositiveSmallIntegerField(help_text="Score 1–10.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assessment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="score_entries",
                        to="investigation.suspectassessment",
                    ),
                ),
                (
                    "scored_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suspect_assessment_scores",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="suspectassessment",
            constraint=models.UniqueConstraint(
                fields=("case", "participant"),
                name="investigation_suspectassessment_unique_case_participant",
            ),
        ),
        migrations.AddConstraint(
            model_name="suspectassessmentscoreentry",
            constraint=models.CheckConstraint(
                condition=models.Q(("score__gte", 1), ("score__lte", 10)),
                name="investigation_scoreentry_score_1_to_10",
            ),
        ),
        migrations.AddIndex(
            model_name="suspectassessment",
            index=models.Index(fields=["case"], name="investigati_case_id_3c0b0d_idx"),
        ),
        migrations.AddIndex(
            model_name="suspectassessmentscoreentry",
            index=models.Index(
                fields=["assessment", "role_key"],
                name="investigati_assessm_8a2c0d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="suspectassessmentscoreentry",
            index=models.Index(fields=["created_at"], name="investigati_created_9e4f2a_idx"),
        ),
    ]
