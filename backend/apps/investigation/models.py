from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class ReasoningSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    case_reference = models.CharField(max_length=64, blank=True)
    title = models.CharField(max_length=150)
    narrative = models.TextField()
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reasoning_submissions",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}:{self.status}"


class ReasoningApproval(models.Model):
    class Decision(models.TextChoices):
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    reasoning = models.OneToOneField(
        ReasoningSubmission,
        on_delete=models.CASCADE,
        related_name="approval",
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reasoning_approvals",
    )
    decision = models.CharField(max_length=20, choices=Decision.choices)
    justification = models.TextField(blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reasoning_id}:{self.decision}"


class SuspectAssessment(models.Model):
    """One assessment container per suspect per case. Holds immutable score history."""

    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="suspect_assessments",
    )
    participant = models.ForeignKey(
        "cases.CaseParticipant",
        on_delete=models.CASCADE,
        related_name="suspect_assessments",
        help_text="Case participant with role suspect.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["case", "participant"],
                name="investigation_suspectassessment_unique_case_participant",
            ),
        ]
        indexes = [
            models.Index(fields=["case"]),
        ]

    def __str__(self):
        return f"Assessment case={self.case_id} participant={self.participant_id}"

    def clean(self):
        if self.participant_id and self.case_id:
            if self.participant.case_id != self.case_id:
                raise ValidationError({"participant": "Participant must belong to this case."})
            if self.participant.role_in_case != "suspect":
                raise ValidationError({"participant": "Participant must have role suspect."})


class SuspectAssessmentScoreEntry(models.Model):
    """Immutable record of a single score (1–10) from detective or sergeant. Append-only."""

    class RoleKey(models.TextChoices):
        DETECTIVE = "detective", "Detective"
        SERGEANT = "sergeant", "Sergeant"

    assessment = models.ForeignKey(
        SuspectAssessment,
        on_delete=models.CASCADE,
        related_name="score_entries",
    )
    scored_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="suspect_assessment_scores",
    )
    role_key = models.CharField(max_length=20, choices=RoleKey.choices)
    score = models.PositiveSmallIntegerField(help_text="Score 1–10.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(score__gte=1) & Q(score__lte=10),
                name="investigation_scoreentry_score_1_to_10",
            ),
        ]
        indexes = [
            models.Index(fields=["assessment", "role_key"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["created_at"]  # immutable history: chronological

    def __str__(self):
        return f"{self.assessment_id}:{self.role_key}={self.score}"

