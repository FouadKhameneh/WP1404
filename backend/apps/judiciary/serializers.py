from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.judiciary.models import CaseVerdict


class CaseVerdictSerializer(serializers.ModelSerializer):
    judge_name = serializers.SerializerMethodField()

    class Meta:
        model = CaseVerdict
        fields = [
            "id",
            "case",
            "judge",
            "judge_name",
            "verdict",
            "punishment_title",
            "punishment_description",
            "recorded_at",
        ]

    def get_judge_name(self, obj):
        if not obj.judge_id:
            return None
        u = get_user_model().objects.filter(pk=obj.judge_id).values_list("full_name", flat=True).first()
        return u or str(obj.judge_id)


class CaseVerdictCreateSerializer(serializers.Serializer):
    verdict = serializers.ChoiceField(choices=CaseVerdict.Verdict.choices)
    punishment_title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    punishment_description = serializers.CharField(required=False, allow_blank=True)
