from django.contrib import admin
from apps.payments.models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "case", "participant", "amount_rials", "gateway_name", "status", "verified_at", "created_at"]
    list_filter = ["status", "gateway_name"]

