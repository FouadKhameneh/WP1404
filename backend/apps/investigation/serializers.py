
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.investigation.models import ReasoningApproval, ReasoningSubmission


class ReasoningSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReasoningSubmission
        fields = ["case_reference", "title", "narrative"]


class ReasoningUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "full_name"]


class ReasoningApprovalSerializer(serializers.ModelSerializer):
    decided_by = ReasoningUserSerializer(read_only=True)

    class Meta:
        model = ReasoningApproval
        fields = ["id", "decision", "justification", "decided_by", "decided_at"]


class ReasoningSubmissionSerializer(serializers.ModelSerializer):
    submitted_by = ReasoningUserSerializer(read_only=True)
    approval = ReasoningApprovalSerializer(read_only=True)

    class Meta:
        model = ReasoningSubmission
        fields = [
            "id",
            "case_reference",
            "title",
            "narrative",
            "status",
            "submitted_by",
            "approval",
            "created_at",
            "updated_at",
        ]


class ReasoningApprovalCreateSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=ReasoningApproval.Decision.choices)
    justification = serializers.CharField(allow_blank=True, required=False)
