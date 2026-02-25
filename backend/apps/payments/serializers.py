from rest_framework import serializers

from apps.payments.models import PaymentTransaction


class PaymentInitiateSerializer(serializers.Serializer):
    case = serializers.IntegerField()
    participant = serializers.IntegerField()
    amount_rials = serializers.IntegerField(min_value=1)
    success_callback_url = serializers.URLField(allow_blank=True, required=False)
    cancel_callback_url = serializers.URLField(allow_blank=True, required=False)


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "case",
            "participant",
            "amount_rials",
            "gateway_name",
            "gateway_ref",
            "status",
            "verified_at",
            "created_at",
        ]
