
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.identity.services import error_response, success_response
from apps.investigation.models import ReasoningApproval, ReasoningSubmission
from apps.investigation.serializers import (
    ReasoningApprovalCreateSerializer,
    ReasoningApprovalSerializer,
    ReasoningSubmissionCreateSerializer,
    ReasoningSubmissionSerializer,
)
from apps.investigation.services import can_approve_reasoning, can_submit_reasoning
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
