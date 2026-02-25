import os
import uuid

from django.conf import settings
from django.db import models


def evidence_attachment_upload_path(instance, filename):
    """Store attachments under evidence/{witness_testimony_id}/{uuid}{ext}."""
    ext = os.path.splitext(filename)[1] or ""
    return f"evidence/witness_testimony/{instance.witness_testimony_id}/{uuid.uuid4().hex}{ext}"


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
