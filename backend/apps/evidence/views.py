from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.evidence.models import BiologicalMedicalEvidence, EvidenceReview
from apps.evidence.serializers import EvidenceReviewCreateSerializer, EvidenceReviewSerializer
from apps.identity.services import error_response, success_response, validation_error_to_details


class BiologicalEvidenceCoronerDecisionAPIView(APIView):
    """
    POST: Submit coroner decision (accept/reject) with follow-up notes for biological/medical evidence.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["evidence.biological_medical.review"]

    def post(self, request, evidence_id):
        evidence = get_object_or_404(
            BiologicalMedicalEvidence.objects.select_related("case"),
            pk=evidence_id,
        )

        serializer = EvidenceReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        decision = serializer.validated_data["decision"]
        follow_up_notes = serializer.validated_data.get("follow_up_notes", "")

        review = EvidenceReview.objects.create(
            biological_medical_evidence=evidence,
            decision=decision,
            follow_up_notes=follow_up_notes,
            reviewed_by=request.user,
        )

        evidence.coroner_status = BiologicalMedicalEvidence.CoronerStatus.RESULT_RECEIVED
        evidence.coroner = request.user
        evidence.result_submitted_at = timezone.now()
        evidence.coroner_result = f"[{review.get_decision_display().upper()}] {follow_up_notes}".strip()
        evidence.save(update_fields=["coroner_status", "coroner", "result_submitted_at", "coroner_result", "updated_at"])

        return success_response(
            {"review": EvidenceReviewSerializer(review).data, "evidence_id": evidence.id},
            status_code=status.HTTP_201_CREATED,
        )


class BiologicalEvidenceReviewListAPIView(APIView):
    """
    GET: List coroner reviews for a biological/medical evidence item.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["evidence.biological_medical.review"]

    def get(self, request, evidence_id):
        evidence = get_object_or_404(BiologicalMedicalEvidence, pk=evidence_id)
        reviews = evidence.reviews.select_related("reviewed_by").order_by("-reviewed_at")
        serializer = EvidenceReviewSerializer(reviews, many=True)
        return success_response({"reviews": serializer.data})
