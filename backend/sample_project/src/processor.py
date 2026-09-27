"""
Sample project — payment processor.
Used by the bundled 'add-parameter' scenario.
"""


class PaymentProcessor:

    def __init__(self, gateway: str) -> None:
        self.gateway = gateway

    def charge(self, amount: float, currency: str = "USD") -> dict:
        """Charge the given amount."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if not currency:
            raise ValueError("Currency must not be empty")
        return {"status": "ok", "amount": amount, "gateway": self.gateway}

    def refund(self, transaction_id: str) -> dict:
        return {"status": "refunded", "id": transaction_id}


def validate_amount(amount: float, max_amount: float = 10_000) -> bool:
    """Validate amount is positive and within limits."""
    return 0 < amount <= max_amount
