from django.conf import settings
from django.db import models


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

