"""
Evidence media service: storage abstraction and metadata persistence.
"""
import hashlib
import hmac
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode

from django.conf import settings


def persist_attachment_metadata(attachment):
    """
    Persist file metadata (file_size) from the uploaded file to the model.
    Call after file is saved. Uses update() to avoid signal recursion.
    """
    if not attachment.file or not attachment.file.name:
        return
    try:
        size = attachment.file.size
        if size is not None and (attachment.file_size is None or attachment.file_size != size):
            type(attachment).objects.filter(pk=attachment.pk).update(file_size=size)
    except (OSError, ValueError):
        pass


def generate_signed_token(media_type: str, media_id: int, expiry_seconds: int = 300) -> str:
    """
    Generate a signed token for temporary media access.
    Token format: base64(type:id:expiry):hmac
    """
    secret = getattr(settings, "SECRET_KEY", "fallback-secret")
    expiry = int(time.time()) + expiry_seconds
    payload = f"{media_type}:{media_id}:{expiry}"
    payload_b64 = urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    signature = hmac.new(
        secret.encode(),
        payload_b64.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_signed_token(token: str) -> tuple[str, int] | None:
    """
    Verify signed token and return (media_type, media_id) if valid, else None.
    """
    try:
        payload_b64, signature = token.rsplit(".", 1)
        payload_b64 = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload = urlsafe_b64decode(payload_b64).decode()
        media_type, media_id_str, expiry_str = payload.split(":", 2)
        expiry = int(expiry_str)
        if expiry < time.time():
            return None
        secret = getattr(settings, "SECRET_KEY", "fallback-secret")
        expected = hmac.new(
            secret.encode(),
            payload_b64.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        return media_type, int(media_id_str)
    except (ValueError, TypeError):
        return None
