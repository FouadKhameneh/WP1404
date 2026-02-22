from apps.notifications.services import log_request_audit_event, summarize_request_payload


class AuditTrailMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            request._audit_payload_summary = summarize_request_payload(request)
        except Exception:
            request._audit_payload_summary = {}
        response = self.get_response(request)
        try:
            log_request_audit_event(request, response, payload_summary=getattr(request, "_audit_payload_summary", {}))
        except Exception:
            pass
        return response
