import uuid

from django.conf import settings
from django.db import models


def generate_reward_claim_id():
    return f"RWD-{uuid.uuid4().hex[:12].upper()}"


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


class RewardTip(models.Model):
    """Tip submission by base user; police officer review then detective final review; unique claim ID on approval."""

    class Status(models.TextChoices):
        PENDING_POLICE = "pending_police", "Pending police review"
        PENDING_DETECTIVE = "pending_detective", "Pending detective review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reward_tips_submitted",
    )
    case_reference = models.CharField(max_length=64, blank=True, help_text="Case number or reference.")
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING_POLICE)
    reviewed_by_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reward_tips_reviewed_as_officer",
    )
    reviewed_by_officer_at = models.DateTimeField(null=True, blank=True)
    reviewed_by_detective = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reward_tips_reviewed_as_detective",
    )
    reviewed_by_detective_at = models.DateTimeField(null=True, blank=True)
    reward_claim_id = models.CharField(max_length=32, unique=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["status"]), models.Index(fields=["reward_claim_id"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Tip {self.id} ({self.status})"
