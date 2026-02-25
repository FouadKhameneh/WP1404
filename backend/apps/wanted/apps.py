from django.apps import AppConfig


class WantedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.wanted"

    def ready(self):
        from apps.wanted import signals  # noqa: F401
