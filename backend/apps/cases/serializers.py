from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import serializers

from apps.cases.models import Case, CaseParticipant, Complaint, ComplaintReview, SceneCaseReport
from apps.cases.validators import (
    validate_case_not_closed_or_invalid,
    validate_national_id,
    validate_non_blank,
    validate_phone,
    validate_rejection_requires_reason,
)


class ComplaintUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "full_name", "email", "phone", "national_id"]


class ComplaintCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["id", "case_number", "title", "level", "source_type", "status", "priority"]


class SceneWitnessInputSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    national_id = serializers.CharField(max_length=32)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_full_name(self, value):
        validate_non_blank(value, "full_name")
        return value.strip()

    def validate_phone(self, value):
        return validate_phone(value)

    def validate_national_id(self, value):
        return validate_national_id(value)


class SceneCaseCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    summary = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    level = serializers.ChoiceField(choices=Case.Level.choices)
    priority = serializers.ChoiceField(choices=Case.Priority.choices, required=False, allow_blank=True)
    scene_occurred_at = serializers.DateTimeField()
    witnesses = SceneWitnessInputSerializer(many=True, min_length=1)

    def validate_title(self, value):
        validate_non_blank(value, "title")
        return value.strip()

    def validate_scene_occurred_at(self, value):
        if value and value > timezone.now():
            raise serializers.ValidationError("Scene occurred at cannot be in the future.")
        return value

    def validate_witnesses(self, value):
        national_ids = set()
        for witness in value:
            national_id = witness.get("national_id", "")
            if national_id in national_ids:
                raise serializers.ValidationError(
                    {"witnesses": "Witness national_id values must be unique."}
                )
            national_ids.add(national_id)
        return value


class SceneCaseReportSerializer(serializers.ModelSerializer):
    reported_by = ComplaintUserSerializer(read_only=True)
    superior_approved_by = ComplaintUserSerializer(read_only=True)

    class Meta:
        model = SceneCaseReport
        fields = [
            "id",
            "scene_occurred_at",
            "reported_by",
            "reported_at",
            "superior_approval_required",
            "superior_approved_by",
            "superior_approved_at",
        ]


class SceneCaseWitnessSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseParticipant
        fields = ["id", "full_name", "phone", "national_id", "notes", "created_at"]


class SceneCaseSerializer(serializers.ModelSerializer):
    created_by = ComplaintUserSerializer(read_only=True)
    scene_report_detail = SceneCaseReportSerializer(read_only=True)
    witnesses = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            "id",
            "case_number",
            "title",
            "summary",
            "level",
            "source_type",
            "status",
            "priority",
            "assigned_role_key",
            "created_by",
            "scene_report_detail",
            "witnesses",
            "created_at",
            "updated_at",
        ]

    def get_witnesses(self, obj):
        queryset = obj.participants.filter(
            role_in_case=CaseParticipant.RoleInCase.WITNESS,
            participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
        ).order_by("id")
        return SceneCaseWitnessSerializer(queryset, many=True).data


class ComplaintSerializer(serializers.ModelSerializer):
    complainant = ComplaintUserSerializer(read_only=True)
    case = ComplaintCaseSerializer(read_only=True)
    invalid_attempt_count = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = [
            "id",
            "case",
            "complainant",
            "description",
            "status",
            "rejection_reason",
            "invalid_attempt_count",
            "reviewed_at",
            "validated_at",
            "invalidated_at",
            "created_at",
            "updated_at",
        ]

    def get_invalid_attempt_count(self, obj):
        try:
            counter = obj.validation_counter
        except Complaint.validation_counter.RelatedObjectDoesNotExist:
            return 0
        return counter.invalid_attempt_count


class ComplaintSubmitSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=5000)
    case_id = serializers.PrimaryKeyRelatedField(
        source="case",
        queryset=Case.objects.filter(source_type=Case.SourceType.COMPLAINT),
        required=False,
        allow_null=True,
    )

    def validate_description(self, value):
        validate_non_blank(value, "description")
        return value.strip()

    def validate_case(self, value):
        validate_case_not_closed_or_invalid(value)
        return value

    def create(self, validated_data):
        return Complaint.objects.create(
            complainant=self.context["request"].user,
            **validated_data,
        )


class ComplaintReviewCreateSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=ComplaintReview.Decision.choices)
    rejection_reason = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate(self, attrs):
        validate_rejection_requires_reason(
            attrs.get("decision", ""),
            attrs.get("rejection_reason", ""),
        )
        return attrs


class ComplaintReviewSerializer(serializers.ModelSerializer):
    reviewer = ComplaintUserSerializer(read_only=True)

    class Meta:
        model = ComplaintReview
        fields = ["id", "decision", "rejection_reason", "reviewer", "reviewed_at"]


class ComplaintResubmitSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=5000)

    def validate_description(self, value):
        validate_non_blank(value, "description")
        return value.strip()


class SuspectAddSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    national_id = serializers.CharField(max_length=32)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_full_name(self, value):
        validate_non_blank(value, "full_name")
        return value.strip()

    def validate_phone(self, value):
        return validate_phone(value)

    def validate_national_id(self, value):
        return validate_national_id(value)


class CaseStatusTransitionSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=Case.Status.choices)

    def validate_new_status(self, value):
        allowed = {
            Case.Status.SUSPECT_ASSESSMENT,
            Case.Status.REFERRAL_READY,
            Case.Status.IN_TRIAL,
            Case.Status.CLOSED,
        }
        if value not in allowed:
            raise serializers.ValidationError(
                f"Invalid transition target. Must be one of: {', '.join(allowed)}"
            )
        return value


class CaseParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseParticipant
        fields = ["id", "participant_kind", "role_in_case", "full_name", "phone", "national_id", "notes", "created_at"]


class CaseListSerializer(serializers.ModelSerializer):
    """Compact serializer for case listing."""

    created_by = ComplaintUserSerializer(read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "case_number",
            "title",
            "summary",
            "level",
            "source_type",
            "status",
            "priority",
            "created_by",
            "created_at",
            "updated_at",
        ]


class TimelineEventSummarySerializer(serializers.Serializer):
    """Summary of a timeline event for case detail."""

    id = serializers.IntegerField()
    event_type = serializers.CharField()
    summary = serializers.CharField()
    payload_summary = serializers.JSONField(default=dict)
    created_at = serializers.DateTimeField()


class CaseParticipantSummarySerializer(serializers.ModelSerializer):
    """Participant summary for case detail nested view."""

    class Meta:
        model = CaseParticipant
        fields = ["id", "participant_kind", "role_in_case", "full_name", "phone", "national_id", "notes", "created_at"]


class CaseDetailSerializer(serializers.ModelSerializer):
    """Full case detail with nested participants and timeline summaries."""

    created_by = ComplaintUserSerializer(read_only=True)
    assigned_to = ComplaintUserSerializer(read_only=True)
    scene_report_detail = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    timeline_summaries = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            "id",
            "case_number",
            "title",
            "summary",
            "level",
            "source_type",
            "status",
            "priority",
            "assigned_to",
            "assigned_role_key",
            "created_by",
            "scene_report_detail",
            "participants",
            "timeline_summaries",
            "submitted_at",
            "under_review_at",
            "investigation_started_at",
            "suspect_assessed_at",
            "referral_ready_at",
            "trial_started_at",
            "closed_at",
            "created_at",
            "updated_at",
        ]

    def get_scene_report_detail(self, obj):
        if obj.source_type != Case.SourceType.SCENE_REPORT:
            return None
        try:
            return SceneCaseReportSerializer(obj.scene_report_detail).data
        except ObjectDoesNotExist:
            return None

    def get_participants(self, obj):
        qs = obj.participants.order_by("role_in_case", "id")
        return CaseParticipantSummarySerializer(qs, many=True).data

    def get_timeline_summaries(self, obj):
        from apps.notifications.models import TimelineEvent

        events = TimelineEvent.objects.filter(case_reference=obj.case_number).order_by("-created_at")[:50]
        return TimelineEventSummarySerializer(events, many=True).data
