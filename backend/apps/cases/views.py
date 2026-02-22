from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.cases.models import Complaint, ComplaintReview
from apps.cases.serializers import (
    ComplaintResubmitSerializer,
    ComplaintReviewCreateSerializer,
    ComplaintReviewSerializer,
    ComplaintSerializer,
    ComplaintSubmitSerializer,
)
from apps.cases.services import can_cadet_review_complaint, create_case_for_complaint_if_missing
from apps.identity.services import error_response, success_response
from apps.notifications.services import log_timeline_event


class ComplaintSubmitAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.complaints.submit"]

    def post(self, request):
        serializer = ComplaintSubmitSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        complaint = serializer.save()
        complaint = Complaint.objects.select_related("complainant", "case").get(pk=complaint.pk)
        log_timeline_event(
            event_type="cases.complaint.submitted",
            actor=request.user,
            summary="Complaint submitted.",
            target_type="cases.complaint",
            target_id=str(complaint.id),
            case_reference=complaint.case.case_number if complaint.case_id else "",
            payload_summary={"status": complaint.status},
        )
        return success_response(ComplaintSerializer(complaint).data, status_code=status.HTTP_201_CREATED)


class ComplaintCadetReviewAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.complaints.review"]

    def post(self, request, complaint_id):
        allowed, message = can_cadet_review_complaint(request.user)
        if not allowed:
            return error_response(
                code="ROLE_POLICY_VIOLATION",
                message=message,
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        complaint = get_object_or_404(Complaint.objects.select_related("complainant", "case"), id=complaint_id)
        if complaint.status not in {Complaint.Status.SUBMITTED, Complaint.Status.CADET_REVIEW}:
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message="Only submitted complaints can be reviewed.",
                details={"status": complaint.status},
                status_code=status.HTTP_409_CONFLICT,
            )

        serializer = ComplaintReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        decision = serializer.validated_data["decision"]
        rejection_reason = serializer.validated_data.get("rejection_reason", "")

        try:
            created_case = None
            if decision == ComplaintReview.Decision.APPROVED:
                created_case, _ = create_case_for_complaint_if_missing(complaint, request.user)
                complaint.refresh_from_db()

            review = ComplaintReview.objects.create(
                complaint=complaint,
                reviewer=request.user,
                decision=decision,
                rejection_reason=rejection_reason,
            )
        except ValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=details,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        complaint = Complaint.objects.select_related("complainant", "case").get(pk=complaint.pk)
        event_type = "cases.complaint.rejected"
        event_summary = "Complaint rejected by cadet."
        if complaint.status == Complaint.Status.VALIDATED:
            event_type = "cases.complaint.validated"
            event_summary = "Complaint validated by cadet."
        elif complaint.status == Complaint.Status.FINAL_INVALID:
            event_type = "cases.complaint.final_invalid"
            event_summary = "Complaint terminally invalidated after third rejection."

        payload_summary = {"status": complaint.status, "decision": decision}
        try:
            payload_summary["invalid_attempt_count"] = complaint.validation_counter.invalid_attempt_count
        except Complaint.validation_counter.RelatedObjectDoesNotExist:
            payload_summary["invalid_attempt_count"] = 0

        log_timeline_event(
            event_type=event_type,
            actor=request.user,
            summary=event_summary,
            target_type="cases.complaint",
            target_id=str(complaint.id),
            case_reference=complaint.case.case_number if complaint.case_id else "",
            payload_summary=payload_summary,
        )

        response_payload = {
            "complaint": ComplaintSerializer(complaint).data,
            "review": ComplaintReviewSerializer(review).data,
        }
        if created_case is not None:
            response_payload["created_case_id"] = created_case.id
        return success_response(response_payload, status_code=status.HTTP_200_OK)


class ComplaintResubmitAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.complaints.resubmit"]

    def post(self, request, complaint_id):
        complaint = get_object_or_404(Complaint.objects.select_related("complainant", "case"), id=complaint_id)
        if not request.user.is_superuser and complaint.complainant_id != request.user.id:
            return error_response(
                code="FORBIDDEN",
                message="You can only re-submit your own complaints.",
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if complaint.status == Complaint.Status.FINAL_INVALID:
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message="Complaint is already terminally invalidated.",
                details={"status": complaint.status},
                status_code=status.HTTP_409_CONFLICT,
            )

        serializer = ComplaintResubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            complaint.resubmit(serializer.validated_data["description"])
        except ValidationError as exc:
            details = exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message="Complaint cannot be re-submitted in current state.",
                details=details,
                status_code=status.HTTP_409_CONFLICT,
            )

        complaint = Complaint.objects.select_related("complainant", "case").get(pk=complaint.pk)
        log_timeline_event(
            event_type="cases.complaint.resubmitted",
            actor=request.user,
            summary="Complaint re-submitted after rejection.",
            target_type="cases.complaint",
            target_id=str(complaint.id),
            case_reference=complaint.case.case_number if complaint.case_id else "",
            payload_summary={"status": complaint.status},
        )
        return success_response(ComplaintSerializer(complaint).data, status_code=status.HTTP_200_OK)
