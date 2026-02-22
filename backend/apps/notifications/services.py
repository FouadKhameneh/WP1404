
import json

from django.http import RawPostDataException

from apps.notifications.models import AuditLog, TimelineEvent

SENSITIVE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SENSITIVE_KEYS = {
    "password",
    "password_confirm",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "national_id",
}


def summarize_payload(data, depth: int = 0):
    if depth > 3:
        return "..."
    if isinstance(data, dict):
        summary = {}
        for key, value in data.items():
            key_name = str(key)
            if key_name.lower() in SENSITIVE_KEYS:
                summary[key_name] = "[REDACTED]"
            else:
                summary[key_name] = summarize_payload(value, depth + 1)
        return summary
    if isinstance(data, list):
        return [summarize_payload(item, depth + 1) for item in data[:10]]
    if isinstance(data, str):
        if len(data) > 200:
            return f"{data[:197]}..."
        return data
    if isinstance(data, (int, float, bool)) or data is None:
        return data
    return str(data)


def summarize_request_payload(request):
    try:
        raw_body = request.body if hasattr(request, "body") else b""
    except RawPostDataException:
        raw_body = getattr(request, "_body", b"")
    if not raw_body:
        try:
            if hasattr(request, "POST"):
                sanitized_post = summarize_payload(dict(request.POST))
                if sanitized_post:
                    return {"keys": sorted(sanitized_post.keys()), "data": sanitized_post}
        except Exception:
            pass
        return {}

    content_type = (request.META.get("CONTENT_TYPE") or "").split(";")[0].strip().lower()
    if content_type == "application/json":
        try:
            parsed = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {"size": len(raw_body), "format": "unknown"}
        sanitized = summarize_payload(parsed)
        if isinstance(sanitized, dict):
            return {"keys": sorted(sanitized.keys()), "data": sanitized}
        return {"data": sanitized}

    if content_type in {"application/x-www-form-urlencoded", "multipart/form-data"}:
        sanitized = summarize_payload(dict(request.POST))
        return {"keys": sorted(sanitized.keys()), "data": sanitized}

    return {"size": len(raw_body), "format": content_type or "unknown"}


def extract_target_from_path(path: str):
    segments = [segment for segment in path.strip("/").split("/") if segment]
    if len(segments) < 3 or segments[0] != "api":
        return "", ""

    resource_segments = []
    target_id = ""
    for segment in segments[2:]:
        if segment.isdigit():
            target_id = segment
            break
        resource_segments.append(segment)

    if not resource_segments:
        return "", target_id

    target_type = ".".join(resource_segments[:2])
    return target_type, target_id


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_audit_event(
    *,
    action: str,
    actor,
    request_method: str,
    request_path: str,
    target_type: str,
    target_id: str,
    status_code: int | None,
    payload_summary,
    ip_address: str | None,
    user_agent: str,
):
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        request_method=request_method,
        request_path=request_path,
        target_type=target_type,
        target_id=target_id,
        status_code=status_code,
        payload_summary=payload_summary or {},
        ip_address=ip_address,
        user_agent=(user_agent or "")[:255],
    )


def log_request_audit_event(request, response, payload_summary=None):
    method = request.method.upper()
    if method not in SENSITIVE_METHODS:
        return None
    if not request.path.startswith("/api/"):
        return None

    actor = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
    summary = payload_summary if payload_summary is not None else summarize_request_payload(request)
    target_type, target_id = extract_target_from_path(request.path)
    action = f"http.{method.lower()}"
    return log_audit_event(
        action=action,
        actor=actor,
        request_method=method,
        request_path=request.path,
        target_type=target_type,
        target_id=target_id,
        status_code=getattr(response, "status_code", None),
        payload_summary=summary,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def log_timeline_event(
    *,
    event_type: str,
    actor,
    summary: str,
    target_type: str = "",
    target_id: str = "",
    case_reference: str = "",
    payload_summary=None,
):
    return TimelineEvent.objects.create(
        actor=actor,
        event_type=event_type,
        case_reference=case_reference,
        target_type=target_type,
        target_id=target_id,
        summary=summary,
        payload_summary=payload_summary or {},
    )
