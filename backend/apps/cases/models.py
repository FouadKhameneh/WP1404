import uuid

from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from django.db import transaction
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


class CaseParticipant(models.Model):
    class ParticipantKind(models.TextChoices):
        PERSONNEL = "personnel", "Personnel"
        CIVILIAN = "civilian", "Civilian"

    class RoleInCase(models.TextChoices):
        COMPLAINANT = "complainant", "Complainant"
        WITNESS = "witness", "Witness"
        SUSPECT = "suspect", "Suspect"
        JUDGE = "judge", "Judge"
        CADET = "cadet", "Cadet"
        POLICE_OFFICER = "police_officer", "Police Officer"
        DETECTIVE = "detective", "Detective"
        SERGEANT = "sergeant", "Sergeant"
        CAPTAIN = "captain", "Captain"
        CHIEF = "chief", "Chief"
        CORONER = "coroner", "Coroner"
        BASE_USER = "base_user", "Base User"

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="participants")
    participant_kind = models.CharField(max_length=20, choices=ParticipantKind.choices)
    role_in_case = models.CharField(max_length=30, choices=RoleInCase.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case_participations",
    )
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    national_id = models.CharField(max_length=32, blank=True)
    notes = models.TextField(blank=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case_participants_added",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "role_in_case"]),
            models.Index(fields=["participant_kind"]),
            models.Index(fields=["user"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(user__isnull=False) | ~Q(full_name=""),
                name="cases_caseparticipant_user_or_full_name",
            ),
            models.UniqueConstraint(
                fields=["case", "role_in_case", "user"],
                condition=Q(user__isnull=False),
                name="cases_caseparticipant_unique_case_role_user",
            ),
            models.UniqueConstraint(
                fields=["case", "role_in_case", "national_id"],
                condition=Q(user__isnull=True) & ~Q(national_id=""),
                name="cases_caseparticipant_unique_case_role_national_id",
            ),
        ]

    def __str__(self):
        return f"{self.case.case_number}:{self.role_in_case}"


class Complaint(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        CADET_REVIEW = "cadet_review", "Cadet Review"
        VALIDATED = "validated", "Validated"
        REJECTED = "rejected", "Rejected"
        FINAL_INVALID = "final_invalid", "Final Invalid"

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="complaints")
    complainant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints_submitted",
    )
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    rejection_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    invalidated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "status"]),
            models.Index(fields=["complainant"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~Q(status="final_invalid") | Q(invalidated_at__isnull=False),
                name="cases_complaint_final_invalid_requires_invalidated_at",
            ),
            models.CheckConstraint(
                condition=~Q(status="validated") | Q(validated_at__isnull=False),
                name="cases_complaint_validated_requires_validated_at",
            ),
        ]

    def __str__(self):
        return f"{self.case.case_number}:{self.pk}"

    def apply_review_decision(self, decision: str, rejection_reason: str):
        now = timezone.now()

        if self.status == self.Status.FINAL_INVALID:
            raise ValidationError({"complaint": "Complaint is already terminally invalidated."})

        if decision == ComplaintReview.Decision.APPROVED:
            self.status = self.Status.VALIDATED
            if self.validated_at is None:
                self.validated_at = now
            self.rejection_reason = ""
        else:
            counter, _ = ComplaintValidationCounter.objects.get_or_create(complaint=self)
            counter.invalid_attempt_count = min(counter.invalid_attempt_count + 1, 3)
            counter.last_rejection_reason = rejection_reason
            counter.save()
            self.rejection_reason = rejection_reason
            if counter.invalid_attempt_count >= 3:
                self.status = self.Status.FINAL_INVALID
                if self.invalidated_at is None:
                    self.invalidated_at = now
                if self.case.status != Case.Status.FINAL_INVALID:
                    self.case.status = Case.Status.FINAL_INVALID
                    self.case.save()
            else:
                self.status = self.Status.REJECTED

        self.reviewed_at = now
        self.save()


class ComplaintValidationCounter(models.Model):
    complaint = models.OneToOneField(
        Complaint,
        on_delete=models.CASCADE,
        related_name="validation_counter",
    )
    invalid_attempt_count = models.PositiveSmallIntegerField(default=0)
    last_rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(invalid_attempt_count__gte=0) & Q(invalid_attempt_count__lte=3),
                name="cases_complaintcounter_attempt_count_between_0_3",
            )
        ]

    def __str__(self):
        return f"{self.complaint_id}:{self.invalid_attempt_count}"


class ComplaintReview(models.Model):
    class Decision(models.TextChoices):
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaint_reviews",
    )
    decision = models.CharField(max_length=20, choices=Decision.choices)
    rejection_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["complaint", "reviewed_at"]),
            models.Index(fields=["decision"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~Q(decision="rejected") | ~Q(rejection_reason=""),
                name="cases_complaintreview_rejected_requires_reason",
            )
        ]

    def __str__(self):
        return f"{self.complaint_id}:{self.decision}"

    def clean(self):
        if self.decision == self.Decision.REJECTED and not self.rejection_reason.strip():
            raise ValidationError({"rejection_reason": "Rejection reason is required for rejected reviews."})

    def save(self, *args, **kwargs):
        self.full_clean()
        is_create = self._state.adding
        with transaction.atomic():
            complaint = Complaint.objects.select_for_update().get(pk=self.complaint_id)
            if is_create and complaint.status == Complaint.Status.FINAL_INVALID:
                raise ValidationError({"complaint": "Complaint is already terminally invalidated."})
            super().save(*args, **kwargs)
            if is_create:
                complaint.apply_review_decision(self.decision, self.rejection_reason)

