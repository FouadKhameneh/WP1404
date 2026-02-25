import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("rewards", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RewardTip",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("case_reference", models.CharField(blank=True, help_text="Case number or reference.", max_length=64)),
                ("subject", models.CharField(blank=True, max_length=200)),
                ("content", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending_police", "Pending police review"),
                            ("pending_detective", "Pending detective review"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending_police",
                        max_length=24,
                    ),
                ),
                ("reviewed_by_officer_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_by_detective_at", models.DateTimeField(blank=True, null=True)),
                ("reward_claim_id", models.CharField(blank=True, editable=False, max_length=32, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "reviewed_by_detective",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reward_tips_reviewed_as_detective",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "reviewed_by_officer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reward_tips_reviewed_as_officer",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "submitted_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reward_tips_submitted",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="rewardtip",
            index=models.Index(fields=["status"], name="rewards_rew_status_idx"),
        ),
        migrations.AddIndex(
            model_name="rewardtip",
            index=models.Index(fields=["reward_claim_id"], name="rewards_rew_claim_id_idx"),
        ),
    ]
