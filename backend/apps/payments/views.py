from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.access.permissions import HasRBACPermissions
from apps.cases.models import Case, CaseParticipant
from apps.identity.services import error_response, success_response
from apps.payments.models import PaymentTransaction
from apps.payments.serializers import PaymentInitiateSerializer, PaymentTransactionSerializer
from apps.payments.services import can_initiate_bail_payment, get_gateway_adapter


class PaymentInitiateAPIView(APIView):
    """Initiate level 2/3 bail/fine payment. Creates transaction and returns gateway redirect URL."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasRBACPermissions]
    permission_codes_by_method = {"POST": ["payments.initiate"]}

    def post(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        case = get_object_or_404(Case.objects.all(), id=serializer.validated_data["case"])
        participant = get_object_or_404(
            CaseParticipant.objects.filter(case=case),
            id=serializer.validated_data["participant"],
        )
        allowed, msg = can_initiate_bail_payment(request.user, case, participant)
        if not allowed:
            return error_response(
                code="WORKFLOW_POLICY_VIOLATION",
                message=msg,
                details={},
                status_code=status.HTTP_403_FORBIDDEN,
            )
        amount_rials = serializer.validated_data["amount_rials"]
        success_url = serializer.validated_data.get("success_callback_url") or ""
        cancel_url = serializer.validated_data.get("cancel_callback_url") or ""
        adapter = get_gateway_adapter()
        transaction = PaymentTransaction.objects.create(
            case=case,
            participant=participant,
            amount_rials=amount_rials,
            gateway_name=adapter.gateway_name,
            status=PaymentTransaction.Status.PENDING,
            created_by=request.user,
        )
        base_url = request.build_absolute_uri("/").rstrip("/")
        callback_url = f"{base_url}/api/v1/payments/callback/?transaction_id={transaction.id}"
        try:
            result = adapter.request_payment(
                amount_rials=amount_rials,
                callback_url=callback_url,
                description=f"Bail/fine case {case.case_number}",
                transaction_id=str(transaction.id),
            )
        except Exception as e:
            transaction.status = PaymentTransaction.Status.FAILED
            transaction.save(update_fields=["status", "updated_at"])
            return error_response(
                code="GATEWAY_ERROR",
                message=str(e),
                details={},
                status_code=status.HTTP_502_BAD_GATEWAY,
            )
        transaction.gateway_ref = result.get("gateway_ref", "")
        transaction.save(update_fields=["gateway_ref", "updated_at"])
        return success_response(
            {
                "transaction_id": transaction.id,
                "redirect_url": result.get("redirect_url", ""),
                "gateway_ref": transaction.gateway_ref,
            },
            status_code=status.HTTP_201_CREATED,
        )


class PaymentCallbackAPIView(APIView):
    """Gateway callback: verify and update transaction. No auth (called by gateway)."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return self._handle_callback(request.GET.dict())

    def post(self, request):
        data = getattr(request, "data", None) or request.POST.dict()
        return self._handle_callback(data)

    def _handle_callback(self, data):
        transaction_id = (data.get("transaction_id") or "").strip()
        if not transaction_id:
            return error_response(
                code="VALIDATION_ERROR",
                message="transaction_id required.",
                details={},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        transaction = PaymentTransaction.objects.filter(id=transaction_id).first()
        if not transaction:
            return error_response(
                code="NOT_FOUND",
                message="Transaction not found.",
                details={},
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if transaction.status != PaymentTransaction.Status.PENDING:
            return success_response(
                {"status": transaction.status, "message": "Already processed."},
                status_code=status.HTTP_200_OK,
            )
        adapter = get_gateway_adapter()
        try:
            result = adapter.verify_callback(data)
        except Exception as e:
            transaction.status = PaymentTransaction.Status.FAILED
            transaction.callback_data = data
            transaction.save(update_fields=["status", "callback_data", "updated_at"])
            return error_response(
                code="GATEWAY_VERIFY_ERROR",
                message=str(e),
                details={},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        transaction.callback_data = data
        transaction.verified_at = timezone.now()
        transaction.status = (
            PaymentTransaction.Status.SUCCESS
            if result.get("success")
            else PaymentTransaction.Status.FAILED
        )
        transaction.save(update_fields=["callback_data", "verified_at", "status", "updated_at"])

        frontend_url = getattr(settings, "PAYMENT_RETURN_BASE_URL", "") or "http://localhost:3000"
        if frontend_url:
            return_url = f"{frontend_url.rstrip('/')}/payment/return?transaction_id={transaction.id}&status={transaction.status}"
            return HttpResponseRedirect(return_url)
        return success_response(
            {"transaction_id": transaction.id, "status": transaction.status},
            status_code=status.HTTP_200_OK,
        )


class PaymentTransactionStatusAPIView(APIView):
    """GET: Retrieve transaction status. For payment return page verification."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, transaction_id):
        transaction = get_object_or_404(PaymentTransaction, id=transaction_id)
        serializer = PaymentTransactionSerializer(transaction)
        return success_response(serializer.data, status_code=status.HTTP_200_OK)
