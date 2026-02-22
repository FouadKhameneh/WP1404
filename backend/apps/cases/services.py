from django.db import transaction

from apps.access.services import user_has_any_role_key
from apps.cases.models import Case, CaseParticipant, Complaint

ROLE_KEY_CADET = "cadet"
ASSIGNED_ROLE_KEY_POLICE_OFFICER = "police_officer"


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
