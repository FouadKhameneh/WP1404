from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.identity.services import error_response, success_response
from apps.rewards.models import RewardTip, generate_reward_claim_id
from apps.rewards.serializers import RewardTipCreateSerializer, RewardTipReviewSerializer, RewardTipSerializer
from apps.rewards.services import can_review_tip_as_detective, can_review_tip_as_officer, can_verify_reward_claim


class RewardTipListCreateAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {
        "GET": ["rewards.tip.view"],
        "POST": ["rewards.tip.submit"],
    }

    def get(self, request):
        queryset = RewardTip.objects.select_related("submitted_by").order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        serializer = RewardTipSerializer(queryset, many=True)
        return success_response({"results": serializer.data}, status_code=status.HTTP_200_OK)

    def post(self, request):
        serializer = RewardTipCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        tip = serializer.save(submitted_by=request.user)
        return success_response(RewardTipSerializer(tip).data, status_code=status.HTTP_201_CREATED)


class RewardTipReviewAPIView(APIView):
    """Police officer first review; detective final review. On detective approve: set unique reward_claim_id."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"POST": ["rewards.tip.review"]}

    def post(self, request, tip_id):
        tip = get_object_or_404(RewardTip.objects.all(), id=tip_id)
        serializer = RewardTipReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        approved = serializer.validated_data["approved"]

        if tip.status == RewardTip.Status.PENDING_POLICE:
            allowed, msg = can_review_tip_as_officer(request.user)
            if not allowed:
                return error_response(
                    code="ROLE_POLICY_VIOLATION",
                    message=msg,
                    details={},
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            tip.reviewed_by_officer = request.user
            tip.reviewed_by_officer_at = timezone.now()
            tip.status = RewardTip.Status.PENDING_DETECTIVE if approved else RewardTip.Status.REJECTED
            tip.save(update_fields=["reviewed_by_officer_id", "reviewed_by_officer_at", "status", "updated_at"])
        elif tip.status == RewardTip.Status.PENDING_DETECTIVE:
            allowed, msg = can_review_tip_as_detective(request.user)
            if not allowed:
                return error_response(
                    code="ROLE_POLICY_VIOLATION",
                    message=msg,
                    details={},
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            tip.reviewed_by_detective = request.user
            tip.reviewed_by_detective_at = timezone.now()
            if approved:
                tip.status = RewardTip.Status.APPROVED
                tip.reward_claim_id = generate_reward_claim_id()
            else:
                tip.status = RewardTip.Status.REJECTED
            tip.save(
                update_fields=[
                    "reviewed_by_detective_id",
                    "reviewed_by_detective_at",
                    "status",
                    "reward_claim_id",
                    "updated_at",
                ]
            )
        else:
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message="Tip is not pending review.",
                details={"status": tip.status},
                status_code=status.HTTP_409_CONFLICT,
            )
        return success_response(RewardTipSerializer(tip).data, status_code=status.HTTP_200_OK)


class RewardClaimVerifyAPIView(APIView):
    """Verify reward claim using National ID + Unique ID. Authorized police ranks only."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"POST": ["rewards.claim.verify"]}

    def post(self, request):
        allowed, message = can_verify_reward_claim(request.user)
        if not allowed:
            return error_response(
                code="ROLE_POLICY_VIOLATION",
                message=message,
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )
        national_id = (request.data.get("national_id") or request.query_params.get("national_id") or "").strip()
        reward_claim_id = (request.data.get("reward_claim_id") or request.query_params.get("reward_claim_id") or "").strip()
        if not national_id or not reward_claim_id:
            return error_response(
                code="VALIDATION_ERROR",
                message="national_id and reward_claim_id are required.",
                details={"national_id": ["Required."] if not national_id else [], "reward_claim_id": ["Required."] if not reward_claim_id else []},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        tip = (
            RewardTip.objects.filter(
                reward_claim_id=reward_claim_id,
                status=RewardTip.Status.APPROVED,
                submitted_by__national_id=national_id,
            )
            .select_related("submitted_by")
            .first()
        )
        if not tip:
            return success_response(
                {"valid": False, "message": "No matching approved claim for this National ID and Unique ID."},
                status_code=status.HTTP_200_OK,
            )
        return success_response(
            {
                "valid": True,
                "reward_claim_id": tip.reward_claim_id,
                "case_reference": tip.case_reference,
                "subject": tip.subject,
                "submitted_at": tip.created_at.isoformat(),
            },
            status_code=status.HTTP_200_OK,
        )
