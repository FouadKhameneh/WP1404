from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RewardComputationSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("national_id", models.CharField(db_index=True, max_length=32)),
                ("full_name", models.CharField(blank=True, max_length=255)),
                ("max_days_lj", models.PositiveIntegerField(help_text="max(Lj): max days under surveillance in one case.")),
                (
                    "max_crime_level_di",
                    models.PositiveSmallIntegerField(
                        help_text="max(Di): max crime level 1-4 (3->1, 2->2, 1->3, critical->4)."
                    ),
                ),
                ("ranking_score", models.PositiveIntegerField(help_text="max(Lj) * max(Di).")),
                ("reward_amount_rials", models.BigIntegerField(help_text="ranking_score * 20,000,000.")),
                ("computed_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-ranking_score", "-computed_at"],
            },
        ),
        migrations.AddIndex(
            model_name="rewardcomputationsnapshot",
            index=models.Index(fields=["computed_at"], name="rewards_rew_compute_idx"),
        ),
        migrations.AddIndex(
            model_name="rewardcomputationsnapshot",
            index=models.Index(fields=["ranking_score"], name="rewards_rew_ranking_idx"),
        ),
    ]
