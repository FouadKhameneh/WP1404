from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.cases.models import Case
from apps.identity.services import error_response, success_response
from apps.judiciary.models import CaseVerdict
from apps.judiciary.serializers import CaseVerdictCreateSerializer, CaseVerdictSerializer
from apps.judiciary.services import build_referral_package, can_record_verdict


class ReferralPackageAPIView(APIView):
    """Referral package endpoint: case summary, participants, evidence for judiciary."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"GET": ["judiciary.referral.view"]}

    def get(self, request, case_id):
        case = get_object_or_404(Case.objects.all(), id=case_id)
        if case.status not in (Case.Status.REFERRAL_READY, Case.Status.IN_TRIAL):
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message="Referral package is only available for cases in referral_ready or in_trial status.",
                details={"status": case.status},
                status_code=status.HTTP_409_CONFLICT,
            )
        data = build_referral_package(case)
        return success_response(data, status_code=status.HTTP_200_OK)


class CaseVerdictAPIView(APIView):
    """Judge trial endpoint: record verdict and punishment; closes case."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {
        "GET": ["judiciary.verdict.view"],
        "POST": ["judiciary.verdict.add"],
    }

    def get(self, request, case_id):
        case = get_object_or_404(Case.objects.all(), id=case_id)
        try:
            verdict = CaseVerdict.objects.get(case=case)
        except CaseVerdict.DoesNotExist:
            return error_response(
                code="NOT_FOUND",
                message="No verdict recorded for this case.",
                details={},
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = CaseVerdictSerializer(verdict)
        return success_response(serializer.data, status_code=status.HTTP_200_OK)

    def post(self, request, case_id):
        allowed, message = can_record_verdict(request.user)
        if not allowed:
            return error_response(
                code="ROLE_POLICY_VIOLATION",
                message=message,
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )
        case = get_object_or_404(Case.objects.all(), id=case_id)
        if case.status != Case.Status.IN_TRIAL:
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message="Verdict can only be recorded for cases in trial.",
                details={"status": case.status},
                status_code=status.HTTP_409_CONFLICT,
            )
        if CaseVerdict.objects.filter(case=case).exists():
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message="Verdict already recorded for this case.",
                details={},
                status_code=status.HTTP_409_CONFLICT,
            )
        serializer = CaseVerdictCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        verdict = CaseVerdict.objects.create(
            case=case,
            judge=request.user,
            verdict=serializer.validated_data["verdict"],
            punishment_title=serializer.validated_data.get("punishment_title", ""),
            punishment_description=serializer.validated_data.get("punishment_description", ""),
        )
        case.status = Case.Status.CLOSED
        case.closed_at = timezone.now()
        case.save(update_fields=["status", "closed_at", "updated_at"])
        response_serializer = CaseVerdictSerializer(verdict)
        return success_response(response_serializer.data, status_code=status.HTTP_201_CREATED)
