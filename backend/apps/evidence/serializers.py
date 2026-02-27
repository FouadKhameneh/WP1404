from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.evidence.models import (
    BiologicalMedicalEvidence,
    Evidence,
    EvidenceLink,
    EvidenceReview,
    IdentificationEvidence,
    OtherEvidence,
    VehicleEvidence,
    WitnessTestimony,
)


class EvidenceNodeSerializer(serializers.ModelSerializer):
    """Minimal evidence data for graph nodes."""

    class Meta:
        model = Evidence
        fields = ["id", "title", "evidence_type"]


class EvidenceLinkSerializer(serializers.ModelSerializer):
    source_node = EvidenceNodeSerializer(source="source", read_only=True)
    target_node = EvidenceNodeSerializer(source="target", read_only=True)
    created_by_display = serializers.SerializerMethodField()

    def get_created_by_display(self, obj):
        return obj.created_by.full_name if obj.created_by else ""

    class Meta:
        model = EvidenceLink
        fields = [
            "id",
            "source",
            "target",
            "source_node",
            "target_node",
            "label",
            "created_by",
            "created_by_display",
            "created_at",
        ]
        read_only_fields = ["created_by", "created_at"]


class EvidenceLinkCreateSerializer(serializers.Serializer):
    source_id = serializers.IntegerField()
    target_id = serializers.IntegerField()
    label = serializers.CharField(required=False, allow_blank=True, max_length=100)


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


# --- Evidence list/detail and create serializers ---


class EvidenceListSerializer(serializers.ModelSerializer):
    """Minimal evidence for list view; handles polymorphic subtypes."""

    registrar_display = serializers.SerializerMethodField()
    evidence_type_display = serializers.CharField(source="get_evidence_type_display", read_only=True)

    def get_registrar_display(self, obj):
        return obj.registrar.full_name if obj.registrar else ""

    class Meta:
        model = Evidence
        fields = [
            "id",
            "title",
            "description",
            "evidence_type",
            "evidence_type_display",
            "registered_at",
            "registrar",
            "registrar_display",
            "case",
            "created_at",
        ]


class WitnessTestimonyCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    transcript = serializers.CharField(required=False, allow_blank=True)
    registered_at = serializers.DateTimeField()


class BiologicalMedicalCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    registered_at = serializers.DateTimeField()


class VehicleEvidenceCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    registered_at = serializers.DateTimeField()
    model = serializers.CharField(max_length=100)
    color = serializers.CharField(max_length=50)
    plate = serializers.CharField(required=False, allow_blank=True, max_length=20)
    serial_number = serializers.CharField(required=False, allow_blank=True, max_length=100)


class IdentificationEvidenceCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    registered_at = serializers.DateTimeField()
    attributes = serializers.JSONField(required=False, default=dict)


class OtherEvidenceCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    registered_at = serializers.DateTimeField()
