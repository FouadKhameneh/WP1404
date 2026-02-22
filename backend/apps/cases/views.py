from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.cases.models import Case, Complaint, ComplaintReview
from apps.cases.serializers import (
    ComplaintResubmitSerializer,
    ComplaintReviewCreateSerializer,
    ComplaintReviewSerializer,
    ComplaintSerializer,
    ComplaintSubmitSerializer,
    SceneCaseCreateSerializer,
    SceneCaseSerializer,
)
from apps.cases.services import (
    can_cadet_review_complaint,
    can_approve_scene_case,
    can_create_scene_case,
    approve_scene_case,
    create_case_for_complaint_if_missing,
    create_scene_case_with_witnesses,
)
from apps.identity.services import error_response, success_response
from apps.notifications.services import log_timeline_event


class SceneCaseCreateAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.scene_cases.create"]

    def post(self, request):
        allowed, message = can_create_scene_case(request.user)
        if not allowed:
            return error_response(
                code="ROLE_POLICY_VIOLATION",
                message=message,
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = SceneCaseCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            case, _ = create_scene_case_with_witnesses(
                actor=request.user,
                title=serializer.validated_data["title"],
                summary=serializer.validated_data.get("summary", ""),
                level=serializer.validated_data["level"],
                priority=serializer.validated_data.get("priority", ""),
                scene_occurred_at=serializer.validated_data["scene_occurred_at"],
                witnesses=serializer.validated_data["witnesses"],
            )
        except (ValidationError, IntegrityError) as exc:
            if isinstance(exc, ValidationError):
                details = exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages}
            else:
                details = {"non_field_errors": ["Scene case payload violates data integrity rules."]}
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=details,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        case = Case.objects.select_related("created_by", "scene_report_detail").get(pk=case.pk)
        witness_count = len(serializer.validated_data["witnesses"])
        log_timeline_event(
            event_type="cases.scene_case.created",
            actor=request.user,
            summary="Scene-based case created.",
            target_type="cases.case",
            target_id=str(case.id),
            case_reference=case.case_number,
            payload_summary={
                "source_type": case.source_type,
                "level": case.level,
                "witness_count": witness_count,
            },
        )
        return success_response(SceneCaseSerializer(case).data, status_code=status.HTTP_201_CREATED)


class SceneCaseApproveAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.scene_cases.approve"]

    def post(self, request, case_id):
        case = get_object_or_404(
            Case.objects.select_related("scene_report_detail", "created_by"),
            id=case_id,
            source_type=Case.SourceType.SCENE_REPORT,
        )
        scene_report = case.scene_report_detail
        allowed, message = can_approve_scene_case(request.user, case, scene_report)
        if not allowed:
            code = "WORKFLOW_POLICY_VIOLATION"
            status_code = status.HTTP_409_CONFLICT
            if message in {
                "Cadet role cannot approve scene-based cases.",
                "Only police roles can approve scene-based cases.",
                "Only the assigned superior role can approve this scene case.",
                "Reporter cannot approve their own scene case.",
            }:
                code = "ROLE_POLICY_VIOLATION"
                status_code = status.HTTP_403_FORBIDDEN
            return error_response(
                code=code,
                message=message,
                details={},
                status_code=status_code,
            )

        approved_case, message = approve_scene_case(actor=request.user, case=case)
        if approved_case is None:
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message=message or "Scene case cannot be approved in current state.",
                details={},
                status_code=status.HTTP_409_CONFLICT,
            )

        approved_case = Case.objects.select_related("created_by", "scene_report_detail").get(pk=approved_case.pk)
        log_timeline_event(
            event_type="cases.scene_case.approved",
            actor=request.user,
            summary="Scene-based case approved by superior.",
            target_type="cases.case",
            target_id=str(approved_case.id),
            case_reference=approved_case.case_number,
            payload_summary={"status": approved_case.status},
        )
        return success_response(SceneCaseSerializer(approved_case).data, status_code=status.HTTP_200_OK)


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
