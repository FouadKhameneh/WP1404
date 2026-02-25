import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evidence", "0007_evidencereview"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EvidenceLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("label", models.CharField(blank=True, help_text="Optional edge label", max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="evidence_links_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outgoing_links",
                        to="evidence.evidence",
                    ),
                ),
                (
                    "target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="incoming_links",
                        to="evidence.evidence",
                    ),
                ),
            ],
            options={
                "verbose_name": "Evidence Link",
                "verbose_name_plural": "Evidence Links",
                "indexes": [
                    models.Index(fields=["source", "target"], name="evidence_ev_source__72a5f0_idx"),
                    models.Index(fields=["target"], name="evidence_ev_target__5e9c7a_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=~models.Q(source=models.F("target")),
                        name="evidence_link_no_self_loop",
                    ),
                ],
            },
        ),
    ]
