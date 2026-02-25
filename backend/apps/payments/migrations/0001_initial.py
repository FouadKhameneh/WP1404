import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("cases", "0005_scenecasereport"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PaymentTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount_rials", models.BigIntegerField()),
                ("gateway_name", models.CharField(max_length=64)),
                ("gateway_ref", models.CharField(blank=True, db_index=True, max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("success", "Success"), ("failed", "Failed")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("callback_data", models.JSONField(blank=True, default=dict)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payment_transactions",
                        to="cases.case",
                    ),
                ),
                (
                    "participant",
                    models.ForeignKey(
                        help_text="Suspect for bail/fine.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payment_transactions",
                        to="cases.caseparticipant",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="payment_transactions_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="paymenttransaction",
            index=models.Index(fields=["status"], name="payments_pa_status_idx"),
        ),
        migrations.AddIndex(
            model_name="paymenttransaction",
            index=models.Index(fields=["created_at"], name="payments_pa_created_idx"),
        ),
    ]
