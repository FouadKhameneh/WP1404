from django.apps import AppConfig


class EvidenceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.evidence"

    def ready(self):
        import apps.evidence.signals  # noqa: F401
