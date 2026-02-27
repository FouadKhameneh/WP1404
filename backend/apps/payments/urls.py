from django.urls import path

from apps.payments.views import PaymentCallbackAPIView, PaymentInitiateAPIView, PaymentTransactionStatusAPIView

urlpatterns = [
    path("initiate/", PaymentInitiateAPIView.as_view(), name="payments-initiate"),
    path("callback/", PaymentCallbackAPIView.as_view(), name="payments-callback"),
    path("transactions/<int:transaction_id>/", PaymentTransactionStatusAPIView.as_view(), name="payments-transaction-status"),
]
