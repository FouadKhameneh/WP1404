from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.cases.models import Case, CaseParticipant, Complaint, ComplaintReview, SceneCaseReport


class ComplaintUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "full_name", "email", "phone", "national_id"]


class ComplaintCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["id", "case_number", "title", "level", "source_type", "status", "priority"]


class SceneWitnessInputSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField()
    national_id = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_phone(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("This field may not be blank.")
        return text

    def validate_national_id(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("This field may not be blank.")
        return text


class SceneCaseCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    summary = serializers.CharField(required=False, allow_blank=True)
    level = serializers.ChoiceField(choices=Case.Level.choices)
    priority = serializers.ChoiceField(choices=Case.Priority.choices, required=False, allow_blank=True)
    scene_occurred_at = serializers.DateTimeField()
    witnesses = SceneWitnessInputSerializer(many=True, min_length=1)

    def validate_title(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("This field may not be blank.")
        return text

    def validate_witnesses(self, value):
        national_ids = set()
        for witness in value:
            national_id = witness["national_id"]
            if national_id in national_ids:
                raise serializers.ValidationError("Witness national_id values must be unique.")
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
    description = serializers.CharField()
    case_id = serializers.PrimaryKeyRelatedField(
        source="case",
        queryset=Case.objects.filter(source_type=Case.SourceType.COMPLAINT),
        required=False,
        allow_null=True,
    )

    def validate_description(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("This field may not be blank.")
        return text

    def validate_case(self, value):
        if value and value.status in {Case.Status.CLOSED, Case.Status.FINAL_INVALID}:
            raise serializers.ValidationError("Cannot attach complaint to a closed or invalidated case.")
        return value

    def create(self, validated_data):
        return Complaint.objects.create(
            complainant=self.context["request"].user,
            **validated_data,
        )


class ComplaintReviewCreateSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=ComplaintReview.Decision.choices)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        decision = attrs.get("decision")
        rejection_reason = attrs.get("rejection_reason", "")
        if decision == ComplaintReview.Decision.REJECTED and not rejection_reason.strip():
            raise serializers.ValidationError({"rejection_reason": ["This field is required for rejection."]})
        return attrs


class ComplaintReviewSerializer(serializers.ModelSerializer):
    reviewer = ComplaintUserSerializer(read_only=True)

    class Meta:
        model = ComplaintReview
        fields = ["id", "decision", "rejection_reason", "reviewer", "reviewed_at"]


class ComplaintResubmitSerializer(serializers.Serializer):
    description = serializers.CharField()

    def validate_description(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("This field may not be blank.")
        return text
