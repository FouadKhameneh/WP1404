"""
Evidence media storage abstraction.

Provides a pluggable storage backend for evidence files.
Default implementation uses Django's default file storage.
Override EVIDENCE_MEDIA_STORAGE in settings to use a custom backend (e.g. S3).
"""
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.module_loading import import_string


def get_evidence_media_storage():
    """Return the configured evidence media storage backend."""
    storage_path = getattr(settings, "EVIDENCE_MEDIA_STORAGE", None)
    if storage_path:
        return import_string(storage_path)()
    return default_storage


class EvidenceMediaStorageMixin:
    """
    Mixin for storage backends that adds evidence-specific behavior.
    Use as base for custom storage (e.g. EvidenceS3Storage).
    """

    # Subclasses can override to add path prefix, bucket, etc.
    location_prefix = "evidence"

    def path(self, name):
        return super().path(name)

    def save(self, name, content, max_length=None):
        return super().save(name, content, max_length)
