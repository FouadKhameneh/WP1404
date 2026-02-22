import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


def generate_case_number():
    return f"CASE-{uuid.uuid4().hex[:12].upper()}"


class Case(models.Model):
    class Level(models.TextChoices):
        LEVEL_1 = "1", "Level 1"
        LEVEL_2 = "2", "Level 2"
        LEVEL_3 = "3", "Level 3"
        CRITICAL = "critical", "Critical"

    class SourceType(models.TextChoices):
        COMPLAINT = "complaint", "Complaint"
        SCENE_REPORT = "scene_report", "Scene Report"

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        ACTIVE_INVESTIGATION = "active_investigation", "Active Investigation"
        SUSPECT_ASSESSMENT = "suspect_assessment", "Suspect Assessment"
        REFERRAL_READY = "referral_ready", "Referral Ready"
        IN_TRIAL = "in_trial", "In Trial"
        CLOSED = "closed", "Closed"
        FINAL_INVALID = "final_invalid", "Final Invalid"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    case_number = models.CharField(max_length=32, unique=True, default=generate_case_number, editable=False)
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    level = models.CharField(max_length=10, choices=Level.choices)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.SUBMITTED)
    priority = models.CharField(max_length=10, choices=Priority.choices, blank=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_cases",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case_assignments_made",
    )
    assigned_role_key = models.CharField(max_length=100, blank=True)
    assignment_notes = models.TextField(blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cases_created",
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    under_review_at = models.DateTimeField(null=True, blank=True)
    investigation_started_at = models.DateTimeField(null=True, blank=True)
    suspect_assessed_at = models.DateTimeField(null=True, blank=True)
    referral_ready_at = models.DateTimeField(null=True, blank=True)
    trial_started_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["level"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["source_type"]),
            models.Index(fields=["assigned_to"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(status="closed", closed_at__isnull=False) | ~Q(status="closed"),
                name="cases_case_closed_requires_closed_at",
            )
        ]

    def __str__(self):
        return self.case_number

    @classmethod
    def priority_for_level(cls, level: str):
        mapping = {
            cls.Level.CRITICAL: cls.Priority.URGENT,
            cls.Level.LEVEL_1: cls.Priority.HIGH,
            cls.Level.LEVEL_2: cls.Priority.MEDIUM,
            cls.Level.LEVEL_3: cls.Priority.LOW,
        }
        return mapping.get(level, cls.Priority.MEDIUM)

    @classmethod
    def status_to_timestamp_field(cls, status: str):
        mapping = {
            cls.Status.SUBMITTED: "submitted_at",
            cls.Status.UNDER_REVIEW: "under_review_at",
            cls.Status.ACTIVE_INVESTIGATION: "investigation_started_at",
            cls.Status.SUSPECT_ASSESSMENT: "suspect_assessed_at",
            cls.Status.REFERRAL_READY: "referral_ready_at",
            cls.Status.IN_TRIAL: "trial_started_at",
            cls.Status.CLOSED: "closed_at",
        }
        return mapping.get(status)

    def _previous_status(self):
        if not self.pk:
            return None
        return type(self).objects.filter(pk=self.pk).values_list("status", flat=True).first()

    def save(self, *args, **kwargs):
        if not self.priority:
            self.priority = self.priority_for_level(self.level)

        if self.assigned_to_id and self.assigned_at is None:
            self.assigned_at = timezone.now()
        if not self.assigned_to_id:
            self.assigned_at = None

        previous_status = self._previous_status()
        if previous_status != self.status:
            timestamp_field = self.status_to_timestamp_field(self.status)
            if timestamp_field and getattr(self, timestamp_field) is None:
                setattr(self, timestamp_field, timezone.now())

        super().save(*args, **kwargs)

