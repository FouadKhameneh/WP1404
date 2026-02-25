
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.investigation.models import (
    ReasoningApproval,
    ReasoningSubmission,
    SuspectAssessment,
    SuspectAssessmentScoreEntry,
)


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
    approval = serializers.SerializerMethodField()

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

    def get_approval(self, obj):
        try:
            return ReasoningApprovalSerializer(obj.approval).data
        except ReasoningApproval.DoesNotExist:
            return None


class ReasoningApprovalCreateSerializer(serializers.Serializer):
    """Sergeant approve/reject with optional rationale (required when rejecting)."""

    decision = serializers.ChoiceField(choices=ReasoningApproval.Decision.choices)
    justification = serializers.CharField(
        allow_blank=True,
        required=False,
        help_text="Rationale for the decision; required when rejecting.",
    )

    def validate(self, attrs):
        if attrs.get("decision") == ReasoningApproval.Decision.REJECTED:
            justification = (attrs.get("justification") or "").strip()
            if not justification:
                raise serializers.ValidationError(
                    {"justification": "Rationale (justification) is required when rejecting."}
                )
        return attrs


# ----- Suspect assessment (detective/sergeant scores 1–10, immutable history) -----


class SuspectAssessmentScoreEntrySerializer(serializers.ModelSerializer):
    """Read-only representation of one immutable score entry."""

    scored_by = ReasoningUserSerializer(read_only=True)

    class Meta:
        model = SuspectAssessmentScoreEntry
        fields = ["id", "scored_by", "role_key", "score", "created_at"]
        read_only_fields = fields


class SuspectAssessmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuspectAssessment
        fields = ["case", "participant"]

    def validate(self, attrs):
        case = attrs["case"]
        participant = attrs["participant"]
        if participant.case_id != case.id:
            raise serializers.ValidationError({"participant": "Participant must belong to this case."})
        if participant.role_in_case != "suspect":
            raise serializers.ValidationError({"participant": "Participant must have role suspect."})
        if SuspectAssessment.objects.filter(case=case, participant=participant).exists():
            raise serializers.ValidationError("Assessment for this case and suspect already exists.")
        return attrs


class SuspectAssessmentSerializer(serializers.ModelSerializer):
    """Assessment with computed detective/sergeant scores and full immutable history."""

    detective_score = serializers.SerializerMethodField()
    sergeant_score = serializers.SerializerMethodField()
    score_entries = SuspectAssessmentScoreEntrySerializer(many=True, read_only=True)
    case_number = serializers.CharField(source="case.case_number", read_only=True)
    participant_display = serializers.SerializerMethodField()

    class Meta:
        model = SuspectAssessment
        fields = [
            "id",
            "case",
            "case_number",
            "participant",
            "participant_display",
            "detective_score",
            "sergeant_score",
            "score_entries",
            "created_at",
        ]

    def get_detective_score(self, obj):
        entry = (
            obj.score_entries.filter(role_key=SuspectAssessmentScoreEntry.RoleKey.DETECTIVE)
            .order_by("-created_at")
            .first()
        )
        return entry.score if entry else None

    def get_sergeant_score(self, obj):
        entry = (
            obj.score_entries.filter(role_key=SuspectAssessmentScoreEntry.RoleKey.SERGEANT)
            .order_by("-created_at")
            .first()
        )
        return entry.score if entry else None

    def get_participant_display(self, obj):
        p = obj.participant
        return p.full_name or (getattr(p.user, "full_name", None) or str(p.user_id) if p.user_id else str(p.id))


class SuspectAssessmentScoreCreateSerializer(serializers.Serializer):
    """Submit a single score (1–10). role_key is set from request.user's role."""

    score = serializers.IntegerField(min_value=1, max_value=10)
