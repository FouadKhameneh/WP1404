
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.identity.services import error_response, success_response
from apps.investigation.models import (
    ReasoningApproval,
    ReasoningSubmission,
    SuspectAssessment,
    SuspectAssessmentScoreEntry,
)
from apps.investigation.serializers import (
    ReasoningApprovalCreateSerializer,
    ReasoningApprovalSerializer,
    ReasoningSubmissionCreateSerializer,
    ReasoningSubmissionSerializer,
    SuspectAssessmentCreateSerializer,
    SuspectAssessmentSerializer,
    SuspectAssessmentScoreCreateSerializer,
    SuspectAssessmentScoreEntrySerializer,
)
from apps.investigation.services import (
    can_approve_reasoning,
    can_create_suspect_assessment,
    can_submit_reasoning,
    can_submit_score_for_assessment,
)
from apps.notifications.services import log_timeline_event


class ReasoningSubmissionListCreateAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {
        "GET": ["investigation.reasoning.view"],
        "POST": ["investigation.reasoning.submit"],
    }

    def get(self, request):
        queryset = ReasoningSubmission.objects.select_related("submitted_by").order_by("-created_at")
        serializer = ReasoningSubmissionSerializer(queryset, many=True)
        return success_response({"results": serializer.data}, status_code=status.HTTP_200_OK)

    def post(self, request):
        allowed, message = can_submit_reasoning(request.user)
        if not allowed:
            return error_response(
                code="ROLE_POLICY_VIOLATION",
                message=message,
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = ReasoningSubmissionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        reasoning = serializer.save(submitted_by=request.user)
        response_serializer = ReasoningSubmissionSerializer(reasoning)
        log_timeline_event(
            event_type="investigation.reasoning.submitted",
            actor=request.user,
            summary="Detective reasoning submitted.",
            target_type="investigation.reasoning",
            target_id=str(reasoning.id),
            case_reference=reasoning.case_reference,
            payload_summary={"title": reasoning.title, "status": reasoning.status},
        )
        return success_response(response_serializer.data, status_code=status.HTTP_201_CREATED)


class ReasoningSubmissionDetailAPIView(APIView):
    """Retrieve a single reasoning submission (for sergeants/detectives to view detail)."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"GET": ["investigation.reasoning.view"]}

    def get(self, request, reasoning_id):
        reasoning = get_object_or_404(
            ReasoningSubmission.objects.select_related(
                "submitted_by", "approval", "approval__decided_by"
            ),
            id=reasoning_id,
        )
        serializer = ReasoningSubmissionSerializer(reasoning)
        return success_response(serializer.data, status_code=status.HTTP_200_OK)


class ReasoningApprovalCreateAPIView(APIView):
    """Sergeant approves or rejects a detective's reasoning submission (with rationale)."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"POST": ["investigation.reasoning.approve"]}

    def post(self, request, reasoning_id):
        reasoning = get_object_or_404(ReasoningSubmission.objects.select_related("submitted_by"), id=reasoning_id)
        allowed, message = can_approve_reasoning(request.user, reasoning)
        if not allowed:
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message=message,
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = ReasoningApprovalCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        approval = ReasoningApproval.objects.create(
            reasoning=reasoning,
            decided_by=request.user,
            decision=serializer.validated_data["decision"],
            justification=serializer.validated_data.get("justification", ""),
        )

        if approval.decision == ReasoningApproval.Decision.APPROVED:
            reasoning.status = ReasoningSubmission.Status.APPROVED
        else:
            reasoning.status = ReasoningSubmission.Status.REJECTED
        reasoning.save(update_fields=["status", "updated_at"])
        timeline_event_type = "investigation.reasoning.approved"
        timeline_summary = "Detective reasoning approved by sergeant."
        if approval.decision == ReasoningApproval.Decision.REJECTED:
            timeline_event_type = "investigation.reasoning.rejected"
            timeline_summary = "Detective reasoning rejected by sergeant."
        log_timeline_event(
            event_type=timeline_event_type,
            actor=request.user,
            summary=timeline_summary,
            target_type="investigation.reasoning",
            target_id=str(reasoning.id),
            case_reference=reasoning.case_reference,
            payload_summary={"decision": approval.decision, "status": reasoning.status},
        )

        response_serializer = ReasoningApprovalSerializer(approval)
        return success_response(response_serializer.data, status_code=status.HTTP_200_OK)


# ----- Suspect assessment: detective/sergeant scores 1–10, immutable history -----


class SuspectAssessmentListCreateAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {
        "GET": ["investigation.suspect_assessment.view"],
        "POST": ["investigation.suspect_assessment.add"],
    }

    def get(self, request):
        queryset = (
            SuspectAssessment.objects.select_related("case", "participant")
            .prefetch_related("score_entries__scored_by")
            .order_by("-created_at")
        )
        case_id = request.query_params.get("case")
        if case_id is not None:
            queryset = queryset.filter(case_id=case_id)
        serializer = SuspectAssessmentSerializer(queryset, many=True)
        return success_response({"results": serializer.data}, status_code=status.HTTP_200_OK)

    def post(self, request):
        allowed, message = can_create_suspect_assessment(request.user)
        if not allowed:
            return error_response(
                code="ROLE_POLICY_VIOLATION",
                message=message,
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = SuspectAssessmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        assessment = serializer.save()
        response_serializer = SuspectAssessmentSerializer(
            SuspectAssessment.objects.prefetch_related("score_entries__scored_by").get(pk=assessment.pk)
        )
        return success_response(response_serializer.data, status_code=status.HTTP_201_CREATED)


class SuspectAssessmentDetailAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"GET": ["investigation.suspect_assessment.view"]}

    def get(self, request, assessment_id):
        assessment = get_object_or_404(
            SuspectAssessment.objects.select_related("case", "participant").prefetch_related(
                "score_entries__scored_by"
            ),
            id=assessment_id,
        )
        serializer = SuspectAssessmentSerializer(assessment)
        return success_response(serializer.data, status_code=status.HTTP_200_OK)


class SuspectAssessmentScoreCreateAPIView(APIView):
    """Append a score (1–10). Detective submits detective score, sergeant submits sergeant score. Immutable."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"POST": ["investigation.suspect_assessment.submit_score"]}

    def post(self, request, assessment_id):
        assessment = get_object_or_404(SuspectAssessment.objects.select_related("case"), id=assessment_id)
        role_key = None
        if can_submit_score_for_assessment(request.user, assessment, "detective")[0]:
            role_key = SuspectAssessmentScoreEntry.RoleKey.DETECTIVE
        elif can_submit_score_for_assessment(request.user, assessment, "sergeant")[0]:
            role_key = SuspectAssessmentScoreEntry.RoleKey.SERGEANT
        if not role_key:
            return error_response(
                code="ROLE_POLICY_VIOLATION",
                message="Only detective or sergeant can submit a score for their role.",
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = SuspectAssessmentScoreCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        entry = SuspectAssessmentScoreEntry.objects.create(
            assessment=assessment,
            scored_by=request.user,
            role_key=role_key,
            score=serializer.validated_data["score"],
        )
        response_serializer = SuspectAssessmentScoreEntrySerializer(entry)
        return success_response(response_serializer.data, status_code=status.HTTP_201_CREATED)
