"""
Payment gateway adapter interface for level 2/3 bail/fine.
Concrete implementations (Zarinpal, IDPay, etc.) implement this interface.
"""
from abc import ABC, abstractmethod


class PaymentGatewayAdapter(ABC):
    """Abstract adapter for payment gateways. Implement for each gateway (Zarinpal, IDPay, etc.)."""

    @property
    @abstractmethod
    def gateway_name(self) -> str:
        """Display name of the gateway."""
        pass

    @abstractmethod
    def request_payment(
        self,
        amount_rials: int,
        callback_url: str,
        description: str,
        transaction_id: str,
        **kwargs,
    ) -> dict:
        """
        Request payment; returns dict with gateway_ref and redirect_url for user.
        Raises on gateway error.
        """
        pass

    @abstractmethod
    def verify_callback(self, request_data: dict) -> dict:
        """
        Verify callback from gateway (e.g. GET/POST params). Returns dict:
        { "success": bool, "gateway_ref": str, "amount_rials": int } or raises.
        """
        pass
