"""
Centralized case state machine.

Flow: Submitted → UnderReview → ActiveInvestigation → SuspectAssessment → ReferralReady → InTrial → Closed

Terminal states: Closed, FinalInvalid (reachable when complaint is terminally invalidated).
"""

from django.db import transaction
from django.utils import timezone

from apps.access.services import get_user_role_keys, user_has_any_role_key
from apps.cases.models import Case, CaseParticipant, Complaint, SceneCaseReport

ROLE_KEY_CADET = "cadet"
ASSIGNED_ROLE_KEY_POLICE_OFFICER = "police_officer"
ASSIGNED_ROLE_KEY_SERGEANT = "sergeant"
ASSIGNED_ROLE_KEY_CAPTAIN = "captain"
ASSIGNED_ROLE_KEY_CHIEF = "chief"
POLICE_ROLE_KEYS = {
    "police_officer",
    "patrol_officer",
    "officer",
    "detective",
    "sergeant",
    "captain",
    "chief",
}

# ---------------------------------------------------------------------------
# Case state machine (central definition)
# Flow: Submitted → UnderReview → ActiveInvestigation → SuspectAssessment →
#       ReferralReady → InTrial → Closed
# ---------------------------------------------------------------------------

CASE_STATE_FLOW = (
    Case.Status.SUBMITTED,
    Case.Status.UNDER_REVIEW,
    Case.Status.ACTIVE_INVESTIGATION,
    Case.Status.SUSPECT_ASSESSMENT,
    Case.Status.REFERRAL_READY,
    Case.Status.IN_TRIAL,
    Case.Status.CLOSED,
)

CASE_STATE_TRANSITIONS = {
    Case.Status.SUBMITTED: {Case.Status.UNDER_REVIEW},
    Case.Status.UNDER_REVIEW: {Case.Status.ACTIVE_INVESTIGATION, Case.Status.FINAL_INVALID},
    Case.Status.ACTIVE_INVESTIGATION: {Case.Status.SUSPECT_ASSESSMENT},
    Case.Status.SUSPECT_ASSESSMENT: {Case.Status.REFERRAL_READY},
    Case.Status.REFERRAL_READY: {Case.Status.IN_TRIAL},
    Case.Status.IN_TRIAL: {Case.Status.CLOSED},
    Case.Status.CLOSED: set(),
    Case.Status.FINAL_INVALID: set(),
}

CASE_TERMINAL_STATES = {Case.Status.CLOSED, Case.Status.FINAL_INVALID}

CASE_INITIAL_STATES = {Case.Status.SUBMITTED, Case.Status.UNDER_REVIEW}


def is_valid_case_status_transition(from_status: str, to_status: str) -> bool:
    """Check if transition from from_status to to_status is valid per state machine."""
    allowed = CASE_STATE_TRANSITIONS.get(from_status, set())
    return to_status in allowed


def get_allowed_next_statuses(from_status: str) -> frozenset:
    """Return allowed target statuses for a given current status."""
    return frozenset(CASE_STATE_TRANSITIONS.get(from_status, set()))


def can_case_transition_to(case: Case, new_status: str) -> bool:
    """Check if case can transition to new_status (state machine only, no role check)."""
    return is_valid_case_status_transition(case.status, new_status)


def can_cadet_review_complaint(user):
    if user_has_any_role_key(user, {ROLE_KEY_CADET}):
        return True, None
    return False, "Only users with the cadet role can review complaints."


def create_case_for_complaint_if_missing(complaint: Complaint, actor):
    with transaction.atomic():
        complaint_locked = (
            Complaint.objects.select_for_update()
            .select_related("complainant", "case")
            .get(pk=complaint.pk)
        )
        if complaint_locked.case_id:
            return complaint_locked.case, False

        case = Case.objects.create(
            title=f"Complaint {complaint_locked.id}",
            summary=complaint_locked.description,
            level=Case.Level.LEVEL_3,
            source_type=Case.SourceType.COMPLAINT,
            status=Case.Status.UNDER_REVIEW,
            assigned_by=actor,
            assigned_role_key=ASSIGNED_ROLE_KEY_POLICE_OFFICER,
            created_by=actor,
        )

        complaint_locked.case = case
        complaint_locked.save(update_fields=["case", "updated_at"])

        if complaint_locked.complainant_id:
            CaseParticipant.objects.get_or_create(
                case=case,
                role_in_case=CaseParticipant.RoleInCase.COMPLAINANT,
                user=complaint_locked.complainant,
                defaults={
                    "participant_kind": CaseParticipant.ParticipantKind.CIVILIAN,
                    "full_name": complaint_locked.complainant.full_name,
                    "phone": complaint_locked.complainant.phone,
                    "national_id": complaint_locked.complainant.national_id,
                    "added_by": actor,
                },
            )

        return case, True


def can_create_scene_case(user):
    role_keys = get_user_role_keys(user)
    if ROLE_KEY_CADET in role_keys:
        return False, "Cadet role cannot create scene-based cases."
    if role_keys.intersection(POLICE_ROLE_KEYS):
        return True, None
    return False, "Only non-cadet police roles can create scene-based cases."


def resolve_scene_case_creator_role(user):
    role_keys = get_user_role_keys(user)
    mapping = [
        ("chief", CaseParticipant.RoleInCase.CHIEF),
        ("captain", CaseParticipant.RoleInCase.CAPTAIN),
        ("sergeant", CaseParticipant.RoleInCase.SERGEANT),
        ("detective", CaseParticipant.RoleInCase.DETECTIVE),
        ("police_officer", CaseParticipant.RoleInCase.POLICE_OFFICER),
        ("patrol_officer", CaseParticipant.RoleInCase.POLICE_OFFICER),
        ("officer", CaseParticipant.RoleInCase.POLICE_OFFICER),
    ]
    for key, role_in_case in mapping:
        if key in role_keys:
            return role_in_case
    return CaseParticipant.RoleInCase.POLICE_OFFICER


def resolve_scene_case_superior_role_key(user):
    role_keys = get_user_role_keys(user)
    if "sergeant" in role_keys:
        return ASSIGNED_ROLE_KEY_CAPTAIN
    if "captain" in role_keys:
        return ASSIGNED_ROLE_KEY_CHIEF
    if "chief" in role_keys:
        return ASSIGNED_ROLE_KEY_CHIEF
    return ASSIGNED_ROLE_KEY_SERGEANT


def create_scene_case_with_witnesses(
    *,
    actor,
    title: str,
    summary: str,
    level: str,
    priority: str,
    scene_occurred_at,
    witnesses: list[dict],
):
    with transaction.atomic():
        case = Case.objects.create(
            title=title,
            summary=summary,
            level=level,
            priority=priority,
            source_type=Case.SourceType.SCENE_REPORT,
            status=Case.Status.UNDER_REVIEW,
            assigned_by=actor,
            assigned_role_key=resolve_scene_case_superior_role_key(actor),
            created_by=actor,
        )

        scene_report = SceneCaseReport.objects.create(
            case=case,
            reported_by=actor,
            scene_occurred_at=scene_occurred_at,
        )

        CaseParticipant.objects.get_or_create(
            case=case,
            role_in_case=resolve_scene_case_creator_role(actor),
            user=actor,
            defaults={
                "participant_kind": CaseParticipant.ParticipantKind.PERSONNEL,
                "full_name": actor.full_name,
                "phone": actor.phone,
                "national_id": actor.national_id,
                "added_by": actor,
            },
        )

        for witness in witnesses:
            CaseParticipant.objects.create(
                case=case,
                participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
                role_in_case=CaseParticipant.RoleInCase.WITNESS,
                full_name=witness.get("full_name", ""),
                phone=witness["phone"],
                national_id=witness["national_id"],
                notes=witness.get("notes", ""),
                added_by=actor,
            )

        return case, scene_report


def can_approve_scene_case(user, case: Case, scene_report: SceneCaseReport):
    if case.source_type != Case.SourceType.SCENE_REPORT:
        return False, "Only scene-based cases can be approved in this flow."
    if scene_report.superior_approved_by_id is not None:
        return False, "Scene case is already approved by a superior."
    if scene_report.reported_by_id == user.id:
        return False, "Reporter cannot approve their own scene case."

    role_keys = get_user_role_keys(user)
    if ROLE_KEY_CADET in role_keys:
        return False, "Cadet role cannot approve scene-based cases."
    if not role_keys.intersection(POLICE_ROLE_KEYS):
        return False, "Only police roles can approve scene-based cases."

    expected_superior = (case.assigned_role_key or "").strip().lower()
    if not expected_superior:
        return False, "Case does not have a superior role assignment."
    if expected_superior not in role_keys and "chief" not in role_keys:
        return False, "Only the assigned superior role can approve this scene case."

    return True, None


def approve_scene_case(*, actor, case: Case):
    with transaction.atomic():
        locked_case = Case.objects.select_for_update().select_related("scene_report_detail").get(pk=case.pk)
        scene_report = locked_case.scene_report_detail
        allowed, message = can_approve_scene_case(actor, locked_case, scene_report)
        if not allowed:
            return None, message

        approved_at = timezone.now()
        scene_report.superior_approved_by = actor
        scene_report.superior_approved_at = approved_at
        scene_report.save(update_fields=["superior_approved_by", "superior_approved_at", "updated_at"])

        locked_case.status = Case.Status.ACTIVE_INVESTIGATION
        locked_case.save()
        return locked_case, None


def can_mark_suspect(user):
    role_keys = get_user_role_keys(user)
    if ROLE_KEY_CADET in role_keys:
        return False, "Cadet role cannot mark suspects."
    if "detective" in role_keys or "sergeant" in role_keys:
        return True, None
    if role_keys.intersection(POLICE_ROLE_KEYS):
        return True, None
    return False, "Only detective or police roles can mark suspects."


def can_transition_case_status(user, case: Case, new_status: str):
    """Check if user can transition case to new_status. Uses centralized state machine."""
    if not is_valid_case_status_transition(case.status, new_status):
        allowed = get_allowed_next_statuses(case.status)
        return False, (
            f"Invalid transition: {case.status} → {new_status}. "
            f"Allowed next: {sorted(allowed) or 'none (terminal state)'}."
        )

    role_keys = get_user_role_keys(user)
    captain_or_chief = "captain" in role_keys or "chief" in role_keys
    judge_role = "judge" in role_keys
    detective_or_sergeant = "detective" in role_keys or "sergeant" in role_keys

    if new_status == Case.Status.SUSPECT_ASSESSMENT and not detective_or_sergeant:
        return False, "Only detective or sergeant can move case to suspect assessment."
    if new_status == Case.Status.REFERRAL_READY and not captain_or_chief:
        return False, "Only captain or chief can refer case to judiciary."
    if new_status in (Case.Status.IN_TRIAL, Case.Status.CLOSED) and not judge_role:
        return False, "Only judge can set case to trial or verdict."

    return True, None


def transition_case_status(*, actor, case: Case, new_status: str):
    allowed, message = can_transition_case_status(actor, case, new_status)
    if not allowed:
        return None, message

    with transaction.atomic():
        locked = Case.objects.select_for_update().get(pk=case.pk)
        if locked.status != case.status:
            return None, "Case status changed; retry."
        locked.status = new_status
        locked.save()
        return locked, None
