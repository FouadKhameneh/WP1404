from apps.access.services import user_has_any_role_key
from apps.cases.models import Case


def build_referral_package(case: Case):
    """Build referral package for judiciary: case summary, participants, evidence list."""
    from apps.evidence.models import Evidence
    from apps.cases.models import CaseParticipant

    participants = list(
        CaseParticipant.objects.filter(case=case).values(
            "id", "role_in_case", "full_name", "national_id", "phone", "notes"
        )
    )
    evidence_qs = Evidence.objects.filter(case=case).values(
        "id", "title", "evidence_type", "description", "registered_at"
    )
    evidence_items = []
    for e in evidence_qs:
        e = dict(e)
        if e.get("registered_at"):
            e["registered_at"] = e["registered_at"].isoformat()
        evidence_items.append(e)
    return {
        "case": {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "summary": case.summary,
            "level": case.level,
            "status": case.status,
            "referral_ready_at": case.referral_ready_at.isoformat() if case.referral_ready_at else None,
        },
        "participants": participants,
        "evidence": evidence_items,
    }


def can_record_verdict(user):
    """Only judge can record trial verdict and punishment."""
    if user_has_any_role_key(user, {"judge"}):
        return True, None
    return False, "Only judge can record verdict and punishment."
