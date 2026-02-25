from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.cases.models import Case, CaseParticipant, Complaint, ComplaintReview
from apps.cases.serializers import (
    CaseDetailSerializer,
    CaseListSerializer,
    CaseParticipantSerializer,
    CaseStatusTransitionSerializer,
    ComplaintCaseSerializer,
    ComplaintResubmitSerializer,
    ComplaintReviewCreateSerializer,
    ComplaintReviewSerializer,
    ComplaintSerializer,
    ComplaintSubmitSerializer,
    SceneCaseCreateSerializer,
    SceneCaseSerializer,
    SuspectAddSerializer,
)
from apps.cases.services import (
    can_cadet_review_complaint,
    can_approve_scene_case,
    can_create_scene_case,
    can_mark_suspect,
    can_transition_case_status,
    approve_scene_case,
    create_case_for_complaint_if_missing,
    create_scene_case_with_witnesses,
    transition_case_status,
)
from apps.identity.services import error_response, success_response
from apps.notifications.services import log_timeline_event


class CaseListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class CaseListAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.cases.view"]

    def get(self, request):
        queryset = Case.objects.select_related("created_by").order_by("-created_at")

        # Filter by status
        status_val = request.query_params.get("status")
        if status_val:
            queryset = queryset.filter(status=status_val)

        # Filter by source_type
        source_type = request.query_params.get("source_type")
        if source_type:
            queryset = queryset.filter(source_type=source_type)

        # Filter by level
        level = request.query_params.get("level")
        if level:
            queryset = queryset.filter(level=level)

        # Search in title, summary, case_number
        search = request.query_params.get("search", "").strip()
        if search:
            q = Q(title__icontains=search) | Q(summary__icontains=search) | Q(case_number__icontains=search)
            queryset = queryset.filter(q)

        # Sort
        sort_by = request.query_params.get("sort", "-created_at")
        allowed_sorts = {
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
            "status",
            "-status",
            "case_number",
            "-case_number",
            "level",
            "-level",
            "priority",
            "-priority",
        }
        if sort_by and sort_by.strip() in allowed_sorts:
            queryset = queryset.order_by(sort_by.strip())

        paginator = CaseListPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = CaseListSerializer(page, many=True)
        payload = {
            "results": serializer.data,
            "count": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "current_page": paginator.page.number,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
        }
        return success_response(payload, status_code=status.HTTP_200_OK)


class CaseDetailAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.cases.view"]

    def get(self, request, case_id):
        case = get_object_or_404(
            Case.objects.select_related(
                "created_by",
                "assigned_to",
                "scene_report_detail",
                "scene_report_detail__reported_by",
                "scene_report_detail__superior_approved_by",
            ).prefetch_related("participants"),
            id=case_id,
        )
        serializer = CaseDetailSerializer(case)
        return success_response(serializer.data, status_code=status.HTTP_200_OK)


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

        if created_case is not None:
            log_timeline_event(
                event_type="cases.case.created",
                actor=request.user,
                summary="Case created from complaint validation.",
                target_type="cases.case",
                target_id=str(created_case.id),
                case_reference=created_case.case_number,
                payload_summary={
                    "source_type": created_case.source_type,
                    "status": created_case.status,
                    "complaint_id": complaint.id,
                },
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


class CaseSuspectAddAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.suspects.add"]

    def post(self, request, case_id):
        allowed, message = can_mark_suspect(request.user)
        if not allowed:
            return error_response(
                code="ROLE_POLICY_VIOLATION",
                message=message,
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        case = get_object_or_404(Case.objects.all(), id=case_id)
        if case.status not in {
            Case.Status.ACTIVE_INVESTIGATION,
            Case.Status.SUSPECT_ASSESSMENT,
        }:
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message="Suspects can only be added during investigation or suspect assessment.",
                details={"status": case.status},
                status_code=status.HTTP_409_CONFLICT,
            )

        serializer = SuspectAddSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        participant = CaseParticipant.objects.create(
            case=case,
            participant_kind=CaseParticipant.ParticipantKind.CIVILIAN,
            role_in_case=CaseParticipant.RoleInCase.SUSPECT,
            full_name=serializer.validated_data["full_name"],
            phone=serializer.validated_data["phone"],
            national_id=serializer.validated_data["national_id"],
            notes=serializer.validated_data.get("notes", ""),
            added_by=request.user,
        )

        log_timeline_event(
            event_type="cases.suspect.marked",
            actor=request.user,
            summary="Suspect marked in case.",
            target_type="cases.case_participant",
            target_id=str(participant.id),
            case_reference=case.case_number,
            payload_summary={
                "suspect_full_name": participant.full_name,
                "national_id": participant.national_id,
            },
        )
        return success_response(
            CaseParticipantSerializer(participant).data,
            status_code=status.HTTP_201_CREATED,
        )


class CaseStatusTransitionAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.case.transition_status"]

    def post(self, request, case_id):
        case = get_object_or_404(Case.objects.all(), id=case_id)
        if case.status in {Case.Status.CLOSED, Case.Status.FINAL_INVALID}:
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message="Cannot transition a closed or invalidated case.",
                details={"status": case.status},
                status_code=status.HTTP_409_CONFLICT,
            )

        serializer = CaseStatusTransitionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        new_status = serializer.validated_data["new_status"]
        allowed, message = can_transition_case_status(request.user, case, new_status)
        if not allowed:
            return error_response(
                code="ROLE_POLICY_VIOLATION"
                if "Only " in (message or "")
                else "WORKFLOW_POLICY_VIOLATION",
                message=message,
                details={},
                status_code=status.HTTP_403_FORBIDDEN
                if "Only " in (message or "")
                else status.HTTP_409_CONFLICT,
            )

        updated_case, message = transition_case_status(
            actor=request.user,
            case=case,
            new_status=new_status,
        )
        if updated_case is None:
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message=message or "Transition failed.",
                details={},
                status_code=status.HTTP_409_CONFLICT,
            )

        event_type_map = {
            Case.Status.SUSPECT_ASSESSMENT: "cases.case.suspect_assessment",
            Case.Status.REFERRAL_READY: "cases.case.referral",
            Case.Status.IN_TRIAL: "cases.case.trial_started",
            Case.Status.CLOSED: "cases.case.verdict",
        }
        summary_map = {
            Case.Status.SUSPECT_ASSESSMENT: "Case moved to suspect assessment.",
            Case.Status.REFERRAL_READY: "Case referred to judiciary.",
            Case.Status.IN_TRIAL: "Case trial started.",
            Case.Status.CLOSED: "Case verdict recorded, case closed.",
        }
        log_timeline_event(
            event_type=event_type_map[new_status],
            actor=request.user,
            summary=summary_map[new_status],
            target_type="cases.case",
            target_id=str(updated_case.id),
            case_reference=updated_case.case_number,
            payload_summary={"status": new_status},
        )

        return success_response(
            ComplaintCaseSerializer(updated_case).data,
            status_code=status.HTTP_200_OK,
        )
