from django.urls import path

from apps.payments.views import PaymentCallbackAPIView, PaymentInitiateAPIView

urlpatterns = [
    path("initiate/", PaymentInitiateAPIView.as_view(), name="payments-initiate"),
    path("callback/", PaymentCallbackAPIView.as_view(), name="payments-callback"),
]
