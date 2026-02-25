from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.evidence.models import BiologicalMedicalEvidence, EvidenceReview


class ReviewerSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "full_name", "email"]


class EvidenceReviewCreateSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=EvidenceReview.Decision.choices)
    follow_up_notes = serializers.CharField(required=False, allow_blank=True, max_length=5000)


class EvidenceReviewSerializer(serializers.ModelSerializer):
    reviewed_by = ReviewerSerializer(read_only=True)
    biological_medical_evidence_title = serializers.CharField(source="biological_medical_evidence.title", read_only=True)

    class Meta:
        model = EvidenceReview
        fields = [
            "id",
            "biological_medical_evidence",
            "biological_medical_evidence_title",
            "decision",
            "follow_up_notes",
            "reviewed_by",
            "reviewed_at",
        ]
        read_only_fields = ["biological_medical_evidence", "reviewed_by", "reviewed_at"]
