from django.db import models


class RewardComputationSnapshot(models.Model):
    """Persisted snapshot of ranking/reward formula: max(Lj)*max(Di) for ranking, * 20,000,000 for reward (rials)."""

    national_id = models.CharField(max_length=32, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    max_days_lj = models.PositiveIntegerField(help_text="max(Lj): max days under surveillance in one case.")
    max_crime_level_di = models.PositiveSmallIntegerField(
        help_text="max(Di): max crime level 1-4 (3->1, 2->2, 1->3, critical->4)."
    )
    ranking_score = models.PositiveIntegerField(help_text="max(Lj) * max(Di).")
    reward_amount_rials = models.BigIntegerField(help_text="ranking_score * 20,000,000.")
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["computed_at"]), models.Index(fields=["ranking_score"])]
        ordering = ["-ranking_score", "-computed_at"]

    def __str__(self):
        return f"{self.national_id}: score={self.ranking_score} reward={self.reward_amount_rials}"
