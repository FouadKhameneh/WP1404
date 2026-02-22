
from apps.access.services import user_has_any_role_key
from apps.investigation.models import ReasoningSubmission

ROLE_KEY_DETECTIVE = "detective"
ROLE_KEY_SERGEANT = "sergeant"


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
