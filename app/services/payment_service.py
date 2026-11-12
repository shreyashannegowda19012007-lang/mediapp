"""
Payment Service for MediApp.
Implements an abstract PaymentProvider interface with strict separation between
DemoPaymentProvider and RazorpayPaymentProvider (real HMAC signature verification).
"""
import hmac
import hashlib
import json
import secrets
from abc import ABC, abstractmethod
from typing import Mapping, Any
from app.config import Config
from app.database import get_db, query_db, transaction

class PaymentProvider(ABC):
    """Abstract interface for payment gateways."""
    @abstractmethod
    def create_payment_order(self, order_id: str, amount: float, currency: str = "INR") -> dict[str, Any]:
        """Creates a provider payment order/intent."""
        pass

    @abstractmethod
    def verify_payment(self, payload: Mapping[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """
        Verifies returned payment data.
        Returns (is_valid, transaction_reference, details)
        """
        pass


class DemoPaymentProvider(PaymentProvider):
    """Simulated local payment provider for demo and automated testing."""
    def create_payment_order(self, order_id: str, amount: float, currency: str = "INR") -> dict[str, Any]:
        demo_provider_order_id = f"demo_order_{secrets.token_hex(8)}"
        return {
            "provider": "demo",
            "provider_order_id": demo_provider_order_id,
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "key": "demo_public_key",
            "notes": "Simulated sandbox transaction. No actual currency will be debited."
        }

    def verify_payment(self, payload: Mapping[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        status = payload.get("status", "success")
        order_id = payload.get("order_id")
        
        if status != "success":
            return False, "", {"error": "Payment simulation indicated failure."}
            
        txn_ref = payload.get("transaction_reference") or f"DEMO_TXN_{order_id}_{secrets.token_hex(4).upper()}"
        return True, txn_ref, {"mode": "demo", "simulated": True}


class RazorpayPaymentProvider(PaymentProvider):
    """Real Razorpay integration using HMAC-SHA256 signature verification."""
    def __init__(self):
        self.key_id = Config.RAZORPAY_KEY_ID
        self.key_secret = Config.RAZORPAY_KEY_SECRET
        self.webhook_secret = Config.RAZORPAY_WEBHOOK_SECRET
        
        # Lazy import of razorpay client
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import razorpay
            self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
        return self._client

    def create_payment_order(self, order_id: str, amount: float, currency: str = "INR") -> dict[str, Any]:
        """Creates an order in Razorpay using official SDK."""
        if not self.key_id or not self.key_secret:
            raise ValueError("Razorpay credentials are not configured on the server.")

        # Razorpay amount is in smallest currency unit (paise for INR)
        amount_in_paise = int(round(amount * 100))
        razorpay_order = self.client.order.create({
            "amount": amount_in_paise,
            "currency": currency,
            "receipt": order_id,
            "payment_capture": 1
        })

        return {
            "provider": "razorpay",
            "provider_order_id": razorpay_order["id"],
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "key": self.key_id
        }

    def verify_payment(self, payload: Mapping[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """Verifies signature returned from Razorpay Checkout."""
        razorpay_order_id = payload.get("razorpay_order_id")
        razorpay_payment_id = payload.get("razorpay_payment_id")
        razorpay_signature = payload.get("razorpay_signature")

        if not (razorpay_order_id and razorpay_payment_id and razorpay_signature):
            return False, "", {"error": "Missing required Razorpay payment confirmation fields."}

        # Verification string: razorpay_order_id + "|" + razorpay_payment_id
        message = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
        generated_signature = hmac.new(
            self.key_secret.encode("utf-8"),
            message,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(generated_signature, razorpay_signature):
            return False, "", {"error": "Razorpay payment signature verification failed."}

        return True, razorpay_payment_id, {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "verified": True
        }

    def verify_webhook_signature(self, raw_body: bytes, signature_header: str) -> bool:
        """Verifies webhook signature using configured webhook secret."""
        if not self.webhook_secret:
            return False
        expected_signature = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature_header)


class PaymentService:
    """Authoritative Payment Processing Manager."""
    @classmethod
    def get_provider(cls) -> PaymentProvider:
        if Config.is_demo():
            return DemoPaymentProvider()
        return RazorpayPaymentProvider()

    @classmethod
    def initiate_payment(cls, order_id: str) -> dict[str, Any]:
        """Prepares a payment order for the specified order."""
        order = query_db("SELECT * FROM orders WHERE id = ?", (order_id,), one=True)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")
        if order["order_status"] == "CANCELLED":
            raise ValueError("Cannot initiate payment for a cancelled order.")
        if order["payment_status"] == "paid":
            raise ValueError("This order has already been paid.")

        provider = cls.get_provider()
        payment_order = provider.create_payment_order(order_id, order["total_amount"], order["currency"])
        
        # Store initiated payment attempt in database
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO payments (order_id, provider, amount, currency, status, transaction_reference, provider_order_id)
            VALUES (?, ?, ?, ?, 'initiated', ?, ?)
        """, (
            order_id,
            payment_order["provider"],
            order["total_amount"],
            order["currency"],
            f"INIT_{order_id}_{secrets.token_hex(4)}",
            payment_order.get("provider_order_id")
        ))
        conn.commit()
        return payment_order

    @classmethod
    def complete_payment(cls, order_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        """
        Validates payment outcome, updates order status to 'paid',
        and preserves payment audit record in an atomic transaction.
        """
        conn = get_db()
        with transaction(conn):
            order = query_db("SELECT * FROM orders WHERE id = ?", (order_id,), one=True, conn=conn)
            if not order:
                raise ValueError(f"Order '{order_id}' not found.")
            if order["order_status"] == "CANCELLED":
                raise ValueError("Cannot complete payment for a cancelled order.")
            if order["payment_status"] == "paid":
                # Idempotent response if already processed
                return {"status": "success", "message": "Order was already marked as paid.", "order_id": order_id}

            provider = cls.get_provider()
            is_valid, txn_ref, details = provider.verify_payment(payload)

            cur = conn.cursor()
            if not is_valid:
                cur.execute("""
                    INSERT INTO payments (order_id, provider, amount, currency, status, transaction_reference, raw_response_json)
                    VALUES (?, ?, ?, ?, 'failed', ?, ?)
                """, (
                    order_id,
                    "demo" if Config.is_demo() else "razorpay",
                    order["total_amount"],
                    order["currency"],
                    f"FAILED_{order_id}_{secrets.token_hex(4)}",
                    json.dumps(details)
                ))
                cur.execute("UPDATE orders SET payment_status = 'failed' WHERE id = ?", (order_id,))
                raise ValueError(details.get("error", "Payment verification failed."))

            # Check for duplicate transaction reference
            existing_txn = query_db(
                "SELECT id FROM payments WHERE transaction_reference = ? AND status = 'success'",
                (txn_ref,),
                one=True,
                conn=conn
            )
            if existing_txn:
                raise ValueError("Duplicate payment transaction detected. Replay rejected.")

            # Record successful payment
            cur.execute("""
                INSERT INTO payments (
                    order_id, provider, amount, currency, status, transaction_reference,
                    provider_order_id, signature, raw_response_json
                ) VALUES (?, ?, ?, ?, 'success', ?, ?, ?, ?)
            """, (
                order_id,
                "demo" if Config.is_demo() else "razorpay",
                order["total_amount"],
                order["currency"],
                txn_ref,
                payload.get("razorpay_order_id"),
                payload.get("razorpay_signature"),
                json.dumps(details)
            ))

            # Update order payment status
            cur.execute("""
                UPDATE orders
                SET payment_status = 'paid', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (order_id,))

            # Add status history
            cur.execute("""
                INSERT INTO order_status_history (order_id, from_status, to_status, changed_by_user_id, role, notes)
                VALUES (?, ?, ?, ?, 'customer', ?)
            """, (order_id, order["order_status"], order["order_status"], order["customer_id"], f"Payment confirmed ({txn_ref})"))

        return {
            "status": "success",
            "message": "Payment verified and recorded successfully.",
            "order_id": order_id,
            "transaction_reference": txn_ref
        }
