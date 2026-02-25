"""
Domain validators for Case, Complaint, and related models.

These validators mirror database constraints and business rules,
used by both model clean() and DRF serializers for consistent validation.
"""
import re
from django.core.exceptions import ValidationError

from apps.cases.models import Case, CaseParticipant, Complaint
from apps.cases.services import (
    CASE_STATE_TRANSITIONS,
    CASE_TERMINAL_STATES,
    is_valid_case_status_transition,
)


# ---------------------------------------------------------------------------
# Shared field validators
# ---------------------------------------------------------------------------

def validate_non_blank(value: str, field_name: str = "field"):
    """Ensure string is not empty after strip."""
    if not value or not str(value).strip():
        raise ValidationError({field_name: ["This field may not be blank."]})


def validate_phone(value: str) -> str:
    """Validate phone format (digits, optional + prefix)."""
    cleaned = str(value).strip()
    if not cleaned:
        raise ValidationError({"phone": ["This field may not be blank."]})
    if not re.match(r"^\+?[\d\s\-]{8,20}$", cleaned):
        raise ValidationError({"phone": ["Enter a valid phone number."]})
    return cleaned


def validate_national_id(value: str) -> str:
    """Validate national ID (typically 10 digits for Iran)."""
    cleaned = str(value).strip()
    if not cleaned:
        raise ValidationError({"national_id": ["This field may not be blank."]})
    if not re.match(r"^\d{8,16}$", cleaned):
        raise ValidationError({"national_id": ["Enter a valid national ID (digits only, 8-16 chars)."]})
    return cleaned


def validate_case_not_closed_or_invalid(case: Case) -> None:
    """Ensure case is not closed or final invalid."""
    if case and case.status in CASE_TERMINAL_STATES:
        raise ValidationError(
            {"case": [f"Cannot attach to a case with status '{case.status}'."]}
        )


def validate_case_status_transition(case: Case, new_status: str) -> None:
    """Ensure case can transition to new_status per state machine."""
    if not is_valid_case_status_transition(case.status, new_status):
        allowed = CASE_STATE_TRANSITIONS.get(case.status, set())
        raise ValidationError(
            {"new_status": [f"Invalid transition from '{case.status}' to '{new_status}'. Allowed: {sorted(allowed) or 'none'}."]}
        )


# ---------------------------------------------------------------------------
# Case validators
# ---------------------------------------------------------------------------

def validate_case_closed_requires_closed_at(status: str, closed_at) -> None:
    """Mirror Case constraint: if status=closed then closed_at must be set."""
    if status == Case.Status.CLOSED and closed_at is None:
        raise ValidationError(
            {"closed_at": ["closed_at is required when status is closed."]}
        )


# ---------------------------------------------------------------------------
# CaseParticipant validators
# ---------------------------------------------------------------------------

def validate_participant_user_or_full_name(
    user, full_name: str, participant_kind: str, role_in_case: str
) -> None:
    """Mirror CaseParticipant constraint: must have user or non-empty full_name."""
    if user is not None:
        return
    name = (full_name or "").strip()
    if not name:
        raise ValidationError(
            {"full_name": ["Either user or full_name must be provided."]}
        )


# ---------------------------------------------------------------------------
# Complaint validators
# ---------------------------------------------------------------------------

def validate_complaint_for_submit(complaint: Complaint) -> None:
    """Validate complaint can be submitted (not final invalid)."""
    if complaint and complaint.status == Complaint.Status.FINAL_INVALID:
        raise ValidationError({"complaint": ["Complaint is terminally invalidated."]})


def validate_complaint_for_review(complaint: Complaint) -> None:
    """Validate complaint can be reviewed."""
    if complaint.status not in {Complaint.Status.SUBMITTED, Complaint.Status.CADET_REVIEW}:
        raise ValidationError(
            {"complaint": ["Only submitted complaints can be reviewed."]}
        )


def validate_complaint_for_resubmit(complaint: Complaint) -> None:
    """Validate complaint can be resubmitted."""
    if complaint.status != Complaint.Status.REJECTED:
        raise ValidationError(
            {"complaint": ["Only rejected complaints can be re-submitted."]}
        )
    from apps.cases.models import ComplaintValidationCounter

    counter = ComplaintValidationCounter.objects.filter(complaint=complaint).first()
    if counter and counter.invalid_attempt_count >= 3:
        raise ValidationError(
            {"complaint": ["Complaint is already terminally invalidated."]}
        )


def validate_rejection_requires_reason(decision: str, rejection_reason: str) -> None:
    """Mirror ComplaintReview constraint: rejected decision requires reason."""
    from apps.cases.models import ComplaintReview

    if decision == ComplaintReview.Decision.REJECTED:
        if not (rejection_reason or "").strip():
            raise ValidationError(
                {"rejection_reason": ["Rejection reason is required for rejected reviews."]}
            )
