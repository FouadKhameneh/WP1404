from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from apps.identity.models import User


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
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details if details is not None else {},
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
