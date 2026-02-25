from rest_framework.views import exception_handler


def _normalize_error_details(details):
    """Ensure details is a dict with string/list values for consistent API response format."""
    if details is None:
        return {}
    if not isinstance(details, dict):
        return {"non_field_errors": [str(details)] if isinstance(details, (list, tuple)) else [str(details)]}

    normalized = {}
    for key, value in details.items():
        if isinstance(value, (list, tuple)):
            normalized[key] = [str(item) for item in value]
        else:
            normalized[key] = [str(value)]
    return normalized


def standard_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    status_code = response.status_code
    details = _normalize_error_details(response.data)

    code = "ERROR"
    message = "Request failed."

    if status_code == 400:
        code = "VALIDATION_ERROR"
        message = "Request validation failed."
    elif status_code == 401:
        code = "UNAUTHORIZED"
        message = "Authentication credentials were invalid or missing."
    elif status_code == 403:
        code = "FORBIDDEN"
        message = "You do not have permission to perform this action."
    elif status_code == 404:
        code = "NOT_FOUND"
        message = "Requested resource was not found."
    elif status_code == 405:
        code = "METHOD_NOT_ALLOWED"
        message = "This method is not allowed for the requested endpoint."
    elif status_code == 429:
        code = "TOO_MANY_REQUESTS"
        message = "Too many requests. Please retry later."
    elif status_code >= 500:
        code = "SERVER_ERROR"
        message = "An internal server error occurred."

    response.data = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }
    return response
