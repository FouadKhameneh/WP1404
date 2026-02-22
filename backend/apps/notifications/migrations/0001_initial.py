import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=120)),
                ("request_method", models.CharField(max_length=10)),
                ("request_path", models.CharField(max_length=255)),
                ("target_type", models.CharField(blank=True, max_length=120)),
                ("target_id", models.CharField(blank=True, max_length=120)),
                ("status_code", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("payload_summary", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TimelineEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=120)),
                ("case_reference", models.CharField(blank=True, max_length=64)),
                ("target_type", models.CharField(blank=True, max_length=120)),
                ("target_id", models.CharField(blank=True, max_length=120)),
                ("summary", models.CharField(max_length=255)),
                ("payload_summary", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="timeline_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["created_at"], name="notificatio_created_8beff0_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["action"], name="notificatio_action_be8180_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["target_type", "target_id"], name="notificatio_target__7d000d_idx"),
        ),
        migrations.AddIndex(
            model_name="timelineevent",
            index=models.Index(fields=["created_at"], name="notificatio_created_07ae21_idx"),
        ),
        migrations.AddIndex(
            model_name="timelineevent",
            index=models.Index(fields=["event_type"], name="notificatio_event_t_a218d8_idx"),
        ),
        migrations.AddIndex(
            model_name="timelineevent",
            index=models.Index(fields=["case_reference"], name="notificatio_case_re_159253_idx"),
        ),
        migrations.AddIndex(
            model_name="timelineevent",
            index=models.Index(fields=["target_type", "target_id"], name="notificatio_target__dd1650_idx"),
        ),
    ]
