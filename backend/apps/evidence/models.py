import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def evidence_attachment_upload_path(instance, filename):
    """Store attachments under evidence/{witness_testimony_id}/{uuid}{ext}."""
    ext = os.path.splitext(filename)[1] or ""
    return f"evidence/witness_testimony/{instance.witness_testimony_id}/{uuid.uuid4().hex}{ext}"


def biological_medical_media_upload_path(instance, filename):
    """Store biological/medical media under evidence/biological_medical/{id}/{uuid}{ext}."""
    ext = os.path.splitext(filename)[1] or ""
    return f"evidence/biological_medical/{instance.biological_medical_evidence_id}/{uuid.uuid4().hex}{ext}"


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


class WitnessTestimony(Evidence):
    """
    Witness testimony evidence subtype with transcript and file attachments.

    Supports image, video, and audio attachments with metadata.
    """

    transcript = models.TextField(blank=True)

    class Meta:
        verbose_name = "Witness Testimony"
        verbose_name_plural = "Witness Testimonies"

    def save(self, *args, **kwargs):
        self.evidence_type = Evidence.EvidenceType.WITNESS_TESTIMONY
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Witness Testimony: {self.title}"


class WitnessTestimonyAttachment(models.Model):
    """
    File attachment for witness testimony with image/video/audio metadata.
    """

    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"

    witness_testimony = models.ForeignKey(
        WitnessTestimony,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to=evidence_attachment_upload_path)
    media_type = models.CharField(max_length=10, choices=MediaType.choices, db_index=True)
    # Metadata: for video/audio
    duration_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds (video/audio)")
    # Metadata: for image/video
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    file_size = models.PositiveBigIntegerField(null=True, blank=True, help_text="Size in bytes")
    mime_type = models.CharField(max_length=100, blank=True)
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Witness Testimony Attachment"
        verbose_name_plural = "Witness Testimony Attachments"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.get_media_type_display()} attachment: {self.file.name}"


class BiologicalMedicalEvidence(Evidence):
    """
    Biological/medical evidence subtype with media references and deferred coroner result.

    Evidence (e.g. blood, hair, fingerprints) requiring coroner or identity-database review.
    Media references store images/photos. Coroner result is initially empty and can be
    filled in later by the coroner.
    """

    class CoronerStatus(models.TextChoices):
        PENDING = "pending", "Pending Coroner Review"
        SUBMITTED = "submitted", "Submitted to Coroner"
        RESULT_RECEIVED = "result_received", "Result Received"

    coroner_status = models.CharField(
        max_length=20,
        choices=CoronerStatus.choices,
        default=CoronerStatus.PENDING,
        db_index=True,
    )
    coroner_result = models.TextField(blank=True, help_text="Coroner or database review result (filled when received)")
    coroner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="biological_medical_reviews",
    )
    result_submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Biological / Medical Evidence"
        verbose_name_plural = "Biological / Medical Evidence"

    def save(self, *args, **kwargs):
        self.evidence_type = Evidence.EvidenceType.BIOLOGICAL_MEDICAL
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Biological/Medical: {self.title}"


class BiologicalMedicalMediaReference(models.Model):
    """
    Media reference (image/video) for biological/medical evidence.
    """

    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    biological_medical_evidence = models.ForeignKey(
        BiologicalMedicalEvidence,
        on_delete=models.CASCADE,
        related_name="media_references",
    )
    file = models.FileField(upload_to=biological_medical_media_upload_path)
    media_type = models.CharField(max_length=10, choices=MediaType.choices, db_index=True, default=MediaType.IMAGE)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Biological/Medical Media Reference"
        verbose_name_plural = "Biological/Medical Media References"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.get_media_type_display()}: {self.file.name}"


class VehicleEvidence(Evidence):
    """
    Vehicle evidence subtype with XOR invariant: exactly one of plate or serial_number.

    Per project spec: model, plate, color recorded. If no plate, serial_number required.
    Plate and serial_number cannot both be set.
    """

    model = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    plate = models.CharField(max_length=20, blank=True, help_text="Required if vehicle has plate; mutually exclusive with serial_number")
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Required if vehicle has no plate; mutually exclusive with plate",
    )

    class Meta:
        verbose_name = "Vehicle Evidence"
        verbose_name_plural = "Vehicle Evidence"
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(plate__gt="") & Q(serial_number="") | Q(plate="") & Q(serial_number__gt="")
                ),
                name="evidence_vehicle_plate_xor_serial",
            ),
        ]

    def save(self, *args, **kwargs):
        self.evidence_type = Evidence.EvidenceType.VEHICLE
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        has_plate = bool(self.plate and self.plate.strip())
        has_serial = bool(self.serial_number and self.serial_number.strip())
        if has_plate and has_serial:
            raise ValidationError("Either plate or serial_number must be set, never both.")
        if not has_plate and not has_serial:
            raise ValidationError("Either plate or serial_number must be set, never neither.")

    def __str__(self):
        return f"Vehicle: {self.model} ({self.plate or self.serial_number})"
