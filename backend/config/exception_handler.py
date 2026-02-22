from rest_framework.views import exception_handler


def standard_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    status_code = response.status_code
    details = response.data

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
