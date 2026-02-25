from django.conf import settings
from django.db import models


class PaymentTransaction(models.Model):
    """Transaction record for level 2/3 bail/fine payments via gateway."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )
    participant = models.ForeignKey(
        "cases.CaseParticipant",
        on_delete=models.CASCADE,
        related_name="payment_transactions",
        help_text="Suspect for bail/fine.",
    )
    amount_rials = models.BigIntegerField()
    gateway_name = models.CharField(max_length=64)
    gateway_ref = models.CharField(max_length=255, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    callback_data = models.JSONField(default=dict, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_transactions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["status"]), models.Index(fields=["created_at"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.id} {self.gateway_ref} ({self.status})"
