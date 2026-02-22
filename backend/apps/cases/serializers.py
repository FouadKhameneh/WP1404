from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.cases.models import Case, Complaint, ComplaintReview


class ComplaintUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "full_name", "email", "phone", "national_id"]


class ComplaintCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["id", "case_number", "title", "level", "source_type", "status", "priority"]


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
