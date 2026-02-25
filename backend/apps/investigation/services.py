
from apps.access.services import user_has_any_role_key
from apps.investigation.models import ReasoningSubmission, SuspectAssessment

ROLE_KEY_DETECTIVE = "detective"
ROLE_KEY_SERGEANT = "sergeant"


def can_submit_score_for_assessment(user, assessment: SuspectAssessment, role_key: str):
    """Check if user can submit a score for the given role (detective or sergeant)."""
    if role_key not in (ROLE_KEY_DETECTIVE, ROLE_KEY_SERGEANT):
        return False, "Invalid role_key."
    if not user_has_any_role_key(user, {role_key}):
        return False, f"Only users with the {role_key} role can submit a {role_key} score."
    return True, None


def can_create_suspect_assessment(user):
    """Check if user can create a suspect assessment (detective or sergeant)."""
    if user_has_any_role_key(user, {ROLE_KEY_DETECTIVE, ROLE_KEY_SERGEANT}):
        return True, None
    return False, "Only detective or sergeant can create suspect assessments."


def can_submit_reasoning(user):
    if user_has_any_role_key(user, {ROLE_KEY_DETECTIVE}):
        return True, None
    return False, "Only users with the detective role can submit reasoning."


def can_approve_reasoning(user, reasoning: ReasoningSubmission):
    if not user_has_any_role_key(user, {ROLE_KEY_SERGEANT}):
        return False, "Only users with the sergeant role can approve or reject reasoning."
    if reasoning.status != ReasoningSubmission.Status.PENDING:
        return False, "Only pending reasoning submissions can be approved or rejected."
    if reasoning.submitted_by_id == user.id:
        return False, "You cannot approve or reject your own reasoning submission."
    if not user_has_any_role_key(reasoning.submitted_by, {ROLE_KEY_DETECTIVE}):
        return False, "Reasoning must be submitted by a detective before sergeant approval."
    return True, None
