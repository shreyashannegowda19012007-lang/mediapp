"""
Payment Processing API Routes for MediApp.
Handles order payment initiation, payment signature verification,
and Razorpay webhook reconciliation.
"""
from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required
from app.services.payment_service import PaymentService, RazorpayPaymentProvider
from app.config import Config
from app.database import query_db

payment_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

@payment_bp.route("/create-order", methods=["POST"])
@login_required
def create_payment_order():
    data = request.get_json() or {}
    order_id = data.get("order_id")
    if not order_id:
        return jsonify({"error": "order_id is required."}), 400

    # Ensure requesting user owns this order or is admin
    user_id = session["user_id"]
    role = session["role"]
    order = query_db("SELECT customer_id FROM orders WHERE id = ?", (order_id,), one=True)
    if not order:
        return jsonify({"error": f"Order '{order_id}' not found."}), 404
    if role != "admin" and order["customer_id"] != user_id:
        return jsonify({"error": "Access denied. You do not own this order."}), 403

    try:
        payment_order = PaymentService.initiate_payment(order_id)
        return jsonify({"status": "success", "payment_order": payment_order})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to initiate payment: {str(e)}"}), 500

@payment_bp.route("/verify", methods=["POST"])
@login_required
def verify_payment():
    data = request.get_json() or {}
    order_id = data.get("order_id")
    if not order_id:
        return jsonify({"error": "order_id is required."}), 400

    user_id = session["user_id"]
    role = session["role"]
    order = query_db("SELECT customer_id FROM orders WHERE id = ?", (order_id,), one=True)
    if not order:
        return jsonify({"error": f"Order '{order_id}' not found."}), 404
    if role != "admin" and order["customer_id"] != user_id:
        return jsonify({"error": "Access denied. You do not own this order."}), 403

    try:
        result = PaymentService.complete_payment(order_id, data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Payment verification error: {str(e)}"}), 500

@payment_bp.route("/webhook", methods=["POST"])
def razorpay_webhook():
    """Handles external Razorpay webhook events with signature verification."""
    if Config.is_demo():
        return jsonify({"message": "Webhooks ignored in demo mode."}), 200

    signature = request.headers.get("X-Razorpay-Signature")
    if not signature:
        return jsonify({"error": "Missing webhook signature header."}), 400

    provider = RazorpayPaymentProvider()
    raw_body = request.get_data()
    
    if not provider.verify_webhook_signature(raw_body, signature):
        return jsonify({"error": "Invalid webhook signature."}), 400

    event_data = request.get_json() or {}
    event = event_data.get("event")
    
    if event == "payment.captured":
        payload = event_data.get("payload", {}).get("payment", {}).get("entity", {})
        receipt_order_id = payload.get("notes", {}).get("order_id") or payload.get("description")
        payment_id = payload.get("id")
        
        if receipt_order_id and payment_id:
            try:
                PaymentService.complete_payment(receipt_order_id, {
                    "razorpay_order_id": payload.get("order_id"),
                    "razorpay_payment_id": payment_id,
                    "razorpay_signature": signature
                })
            except Exception as e:
                import logging
                logging.getLogger("mediapp").warning(f"Webhook payment completion skipped for order '{receipt_order_id}': {e}")

    return jsonify({"status": "received"}), 200
