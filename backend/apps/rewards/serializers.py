from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.rewards.models import RewardTip


class RewardTipCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardTip
        fields = ["case_reference", "subject", "content"]


class RewardTipReviewSerializer(serializers.Serializer):
    approved = serializers.BooleanField()


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "full_name"]


class RewardTipSerializer(serializers.ModelSerializer):
    submitted_by = UserBriefSerializer(read_only=True)

    class Meta:
        model = RewardTip
        fields = [
            "id",
            "submitted_by",
            "case_reference",
            "subject",
            "content",
            "status",
            "reviewed_by_officer",
            "reviewed_by_officer_at",
            "reviewed_by_detective",
            "reviewed_by_detective_at",
            "reward_claim_id",
            "created_at",
            "updated_at",
        ]
