from rest_framework import serializers

from apps.wanted.models import Wanted


class WantedSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="case.case_number", read_only=True)
    participant_display = serializers.SerializerMethodField()

    class Meta:
        model = Wanted
        fields = [
            "id",
            "case",
            "case_number",
            "participant",
            "participant_display",
            "marked_at",
            "status",
            "promoted_at",
        ]

    def get_participant_display(self, obj):
        p = obj.participant
        return {
            "full_name": p.full_name or "",
            "national_id": p.national_id or "",
            "phone": p.phone or "",
        }
