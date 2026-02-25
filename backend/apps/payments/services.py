from django.conf import settings
from django.utils import timezone

from apps.cases.models import Case
from apps.payments.models import PaymentTransaction


def get_gateway_adapter():
    """Return configured gateway adapter. Default: Mock for development."""
    from apps.payments.adapters import MockGatewayAdapter
    adapter_class = getattr(settings, "PAYMENT_GATEWAY_ADAPTER", None) or MockGatewayAdapter
    if isinstance(adapter_class, str):
        from django.utils.module_loading import import_string
        adapter_class = import_string(adapter_class)
    return adapter_class() if callable(adapter_class) else adapter_class


def can_initiate_bail_payment(user, case: Case, participant) -> tuple[bool, str]:
    """Level 2/3 only; participant must be suspect in case."""
    if case.level not in (Case.Level.LEVEL_2, Case.Level.LEVEL_3):
        return False, "Bail/fine payment is only for level 2 or 3 cases."
    if participant.case_id != case.id:
        return False, "Participant must belong to this case."
    if participant.role_in_case != "suspect":
        return False, "Participant must be a suspect."
    return True, ""
