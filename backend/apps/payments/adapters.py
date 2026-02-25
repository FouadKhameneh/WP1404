"""Concrete gateway adapters. Mock adapter for development/testing."""
from apps.payments.gateway import PaymentGatewayAdapter


class MockGatewayAdapter(PaymentGatewayAdapter):
    """Mock adapter for tests and development. No real payment."""

    @property
    def gateway_name(self) -> str:
        return "mock"

    def request_payment(
        self,
        amount_rials: int,
        callback_url: str,
        description: str,
        transaction_id: str,
        **kwargs,
    ) -> dict:
        return {
            "gateway_ref": f"MOCK-{transaction_id}",
            "redirect_url": f"{callback_url}?status=ok&ref=MOCK-{transaction_id}&transaction_id={transaction_id}",
        }

    def verify_callback(self, request_data: dict) -> dict:
        ref = (request_data.get("ref") or request_data.get("gateway_ref") or "").strip()
        tid = (request_data.get("transaction_id") or "").strip()
        if ref and ref.startswith("MOCK-"):
            return {"success": True, "gateway_ref": ref, "amount_rials": 0, "transaction_id": tid}
        return {"success": False, "gateway_ref": ref or "", "amount_rials": 0}
