from django.conf import settings
from django.db import models


class Evidence(models.Model):
    """
    Base Evidence model with shared fields and type discriminator.

    All evidence types share: title, description, registered_at, registrar, case.
    The evidence_type field discriminates between different evidence kinds
    (witness testimony, biological/medical, vehicles, identification, other).
    """

    class EvidenceType(models.TextChoices):
        WITNESS_TESTIMONY = "witness_testimony", "Witness / Local Testimony"
        BIOLOGICAL_MEDICAL = "biological_medical", "Found: Biological / Medical"
        VEHICLE = "vehicle", "Found: Vehicle"
        IDENTIFICATION = "identification", "Found: Identification Document"
        OTHER = "other", "Other Evidence"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    evidence_type = models.CharField(
        max_length=30,
        choices=EvidenceType.choices,
        db_index=True,
    )
    registered_at = models.DateTimeField()
    registrar = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evidence_registered",
    )
    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="evidence_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "evidence_type"]),
            models.Index(fields=["registered_at"]),
        ]
        ordering = ["-registered_at", "-created_at"]
        verbose_name = "Evidence"
        verbose_name_plural = "Evidence"

    def __str__(self):
        return f"{self.get_evidence_type_display()}: {self.title}"
