from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from apps.identity.models import User


def validation_error_to_details(exc):
    """Convert Django or DRF ValidationError to consistent details dict."""
    if hasattr(exc, "message_dict") and exc.message_dict:
        return {k: [str(m) for m in (v if isinstance(v, (list, tuple)) else [v])] for k, v in exc.message_dict.items()}
    if hasattr(exc, "messages") and exc.messages:
        return {"non_field_errors": [str(m) for m in exc.messages]}
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, dict):
            return {k: [str(m) for m in (v if isinstance(v, (list, tuple)) else [v])] for k, v in detail.items()}
        if isinstance(detail, (list, tuple)):
            return {"non_field_errors": [str(m) for m in detail]}
        return {"non_field_errors": [str(detail)]}
    return {"non_field_errors": [str(exc)]}


def normalize_error_details(details):
    """Ensure details dict has string values in lists for consistent API format."""
    if details is None:
        return {}
    if not isinstance(details, dict):
        return {"non_field_errors": [str(details)]}
    return {str(k): [str(m) for m in (v if isinstance(v, (list, tuple)) else [v])] for k, v in details.items()}


def find_user_by_identifier(identifier: str):
    normalized = identifier.strip()
    if not normalized:
        return None
    lookup_order = [
        Q(username__iexact=normalized),
        Q(email__iexact=normalized),
        Q(phone=normalized),
        Q(national_id=normalized),
    ]
    for query in lookup_order:
        user = User.objects.filter(query).first()
        if user is not None:
            return user
    return None


def error_response(code: str, message: str, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    normalized = normalize_error_details(details) if details is not None else {}
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": normalized,
        },
    }
    return Response(payload, status=status_code)


def success_response(data, status_code=status.HTTP_200_OK):
    return Response(
        {
            "success": True,
            "data": data,
        },
        status=status_code,
    )
