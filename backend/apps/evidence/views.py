from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.evidence.models import (
    BiologicalMedicalEvidence,
    BiologicalMedicalMediaReference,
    Evidence,
    EvidenceLink,
    EvidenceReview,
    WitnessTestimonyAttachment,
)
from apps.evidence.serializers import (
    EvidenceLinkCreateSerializer,
    EvidenceLinkSerializer,
    EvidenceReviewCreateSerializer,
    EvidenceReviewSerializer,
)
from apps.evidence.services.media import generate_signed_token, verify_signed_token
from apps.identity.services import error_response, success_response
from apps.notifications.services import log_timeline_event


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

        case_reference = evidence.case.case_number if evidence.case_id else ""
        log_timeline_event(
            event_type="evidence.biological_medical.reviewed",
            actor=request.user,
            summary=f"Biological/medical evidence reviewed: {review.get_decision_display()} — {evidence.title}",
            target_type="evidence.evidence",
            target_id=str(evidence.pk),
            case_reference=case_reference,
            payload_summary={
                "decision": decision,
                "evidence_id": evidence.id,
            },
        )

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


# --- Protected media endpoints ---

MEDIA_TYPE_WITNESS = "witness-testimony"
MEDIA_TYPE_BIOLOGICAL = "biological-medical"
SIGNED_URL_EXPIRY = 300  # seconds


def _get_attachment_and_check_access(media_type: str, media_id: int, user=None):
    """Resolve attachment by type/id. When user is provided, caller must enforce case access (e.g. via permission)."""
    if media_type == MEDIA_TYPE_WITNESS:
        attachment = get_object_or_404(
            WitnessTestimonyAttachment.objects.select_related("witness_testimony__case"),
            pk=media_id,
        )
        case = attachment.witness_testimony.case
    elif media_type == MEDIA_TYPE_BIOLOGICAL:
        attachment = get_object_or_404(
            BiologicalMedicalMediaReference.objects.select_related("biological_medical_evidence__case"),
            pk=media_id,
        )
        case = attachment.biological_medical_evidence.case
    else:
        return None, "Unknown media type."
    return attachment, case


def _stream_file_response(attachment):
    """Stream file from attachment, returning FileResponse or error."""
    if not attachment.file or not attachment.file.name:
        return None
    try:
        file_handle = attachment.file.open("rb")
        response = FileResponse(file_handle, as_attachment=False)
        if attachment.mime_type:
            response["Content-Type"] = attachment.mime_type
        if attachment.file_size:
            response["Content-Length"] = attachment.file_size
        return response
    except (OSError, ValueError):
        return None


class EvidenceMediaStreamAPIView(APIView):
    """
    GET: Stream evidence media file. Requires authentication and cases.cases.view permission.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.cases.view"]

    def get(self, request, media_type, media_id):
        attachment, case = _get_attachment_and_check_access(media_type, int(media_id), request.user)
        if case is None:
            return error_response(
                code="INVALID_MEDIA",
                message=attachment or "Invalid media reference.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        response = _stream_file_response(attachment)
        if response is None:
            return error_response(
                code="FILE_NOT_FOUND",
                message="Media file not found or inaccessible.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return response


class EvidenceMediaSignedURLApiView(APIView):
    """
    POST: Get a signed URL for temporary media access.
    Body: { "media_type": "witness-testimony"|"biological-medical", "media_id": <int> }
    Returns: { "url": "...", "token": "...", "expires_in": 300 }
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.cases.view"]

    def post(self, request):
        media_type = request.data.get("media_type")
        media_id = request.data.get("media_id")
        if not media_type or media_id is None:
            return error_response(
                code="VALIDATION_ERROR",
                message="media_type and media_id are required.",
                details={"media_type": media_type or "missing", "media_id": media_id},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if media_type not in (MEDIA_TYPE_WITNESS, MEDIA_TYPE_BIOLOGICAL):
            return error_response(
                code="VALIDATION_ERROR",
                message="media_type must be witness-testimony or biological-medical.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            media_id = int(media_id)
        except (TypeError, ValueError):
            return error_response(
                code="VALIDATION_ERROR",
                message="media_id must be an integer.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        attachment, case = _get_attachment_and_check_access(media_type, media_id, request.user)
        if case is None:
            return error_response(
                code="NOT_FOUND",
                message=attachment or "Media not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        token = generate_signed_token(media_type, media_id, expiry_seconds=SIGNED_URL_EXPIRY)
        base_url = request.build_absolute_uri("/").rstrip("/")
        url = f"{base_url}/api/v1/evidence/media/access/?token={token}"
        return success_response({
            "url": url,
            "token": token,
            "expires_in": SIGNED_URL_EXPIRY,
        })


class EvidenceMediaAccessByTokenAPIView(APIView):
    """
    GET: Access media by signed token. No auth required; token is the credential.
    Use for img/video src when you have a short-lived signed URL.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        token = request.query_params.get("token")
        if not token:
            return error_response(
                code="MISSING_TOKEN",
                message="token query parameter is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        parsed = verify_signed_token(token)
        if not parsed:
            return error_response(
                code="INVALID_TOKEN",
                message="Token is invalid or expired.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        media_type, media_id = parsed
        attachment, case = _get_attachment_and_check_access(media_type, media_id, None)
        if case is None:
            return error_response(
                code="NOT_FOUND",
                message="Media not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        response = _stream_file_response(attachment)
        if response is None:
            return error_response(
                code="FILE_NOT_FOUND",
                message="Media file not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return response


# --- Evidence links (detective board graph) ---


class EvidenceLinkListCreateAPIView(APIView):
    """
    GET: List evidence links. Filter by case_id or evidence_id.
    POST: Create a link between two evidence items.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.cases.view"]

    def get(self, request):
        qs = EvidenceLink.objects.select_related("source", "target", "created_by").order_by("-created_at")
        case_id = request.query_params.get("case_id")
        evidence_id = request.query_params.get("evidence_id")
        if case_id:
            qs = qs.filter(source__case_id=case_id)
        if evidence_id:
            qs = qs.filter(Q(source_id=evidence_id) | Q(target_id=evidence_id))
        serializer = EvidenceLinkSerializer(qs, many=True)
        return success_response({"links": serializer.data})

    def post(self, request):
        serializer = EvidenceLinkCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        source_id = serializer.validated_data["source_id"]
        target_id = serializer.validated_data["target_id"]
        label = serializer.validated_data.get("label", "")
        if source_id == target_id:
            return error_response(
                code="VALIDATION_ERROR",
                message="Source and target cannot be the same.",
                details={"source_id": source_id, "target_id": target_id},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        source = get_object_or_404(Evidence.objects.select_related("case"), pk=source_id)
        target = get_object_or_404(Evidence.objects.select_related("case"), pk=target_id)
        if source.case_id != target.case_id:
            return error_response(
                code="VALIDATION_ERROR",
                message="Source and target must belong to the same case.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        link = EvidenceLink.objects.create(
            source=source,
            target=target,
            label=label,
            created_by=request.user,
        )
        return success_response(
            {"link": EvidenceLinkSerializer(link).data},
            status_code=status.HTTP_201_CREATED,
        )


class EvidenceLinkDetailAPIView(APIView):
    """
    GET: Retrieve a single link.
    DELETE: Remove a link.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    required_permission_codes = ["cases.cases.view"]

    def get(self, request, link_id):
        link = get_object_or_404(
            EvidenceLink.objects.select_related("source", "target", "created_by"),
            pk=link_id,
        )
        return success_response({"link": EvidenceLinkSerializer(link).data})

    def delete(self, request, link_id):
        link = get_object_or_404(EvidenceLink, pk=link_id)
        link.delete()
        return success_response({"deleted": True}, status_code=status.HTTP_200_OK)
