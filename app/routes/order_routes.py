"""
Order Management Routes for MediApp.
Operates as the single authoritative order gateway shared across Customer,
Pharmacy, Delivery, and Admin portals.
"""
import json
from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required
from app.services.order_service import OrderService
from app.database import query_db, get_db

order_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

def format_order_response(o, user_id=None, role=None):
    d = dict(o)
    d["status"] = d.get("order_status", "PLACED")
    d["order_number"] = d.get("id")
    # Redact delivery OTP for non-owner or non-customer
    if role != "customer" or (user_id is not None and d.get("customer_id") != user_id):
        d["delivery_otp"] = None
    addr_raw = d.get("delivery_address_json")
    if addr_raw and not d.get("delivery_address"):
        try:
            parsed = json.loads(addr_raw)
            if isinstance(parsed, dict):
                d["delivery_address"] = f"{parsed.get('line1', '')}, {parsed.get('city', '')} {parsed.get('pincode', '')}".strip(", ")
            else:
                d["delivery_address"] = str(parsed)
        except Exception:
            d["delivery_address"] = str(addr_raw).strip('"')
    return d

@order_bp.route("", methods=["POST"])
@login_required
def create_order():
    """
    Creates an order from current cart or explicitly supplied items.
    Validates delivery address, prescription requirements, inventory availability,
    and calculates authoritative order totals.
    """
    data = request.get_json() or {}
    user_id = session["user_id"]
    raw_addr = data.get("delivery_address")
    if isinstance(raw_addr, dict):
        delivery_address = raw_addr
        addr_str = " ".join(str(v) for v in raw_addr.values() if v).strip()
        if not addr_str or len(addr_str) < 10:
            return jsonify({"error": "A valid delivery address of at least 10 characters is required."}), 400
    elif isinstance(raw_addr, str):
        delivery_address = raw_addr.strip()
        if not delivery_address or len(delivery_address) < 10:
            return jsonify({"error": "A valid delivery address of at least 10 characters is required."}), 400
    else:
        return jsonify({"error": "Delivery address is required."}), 400

    prescription_id = data.get("prescription_id")
    delivery_notes = data.get("delivery_notes")

    # Support items supplied directly or retrieved from user's current cart
    raw_items = data.get("items") or data.get("cart_items")
    if raw_items and isinstance(raw_items, list) and len(raw_items) > 0:
        pharmacy_id = data.get("pharmacy_id", 1)
        cart_items = []
        for it in raw_items:
            mid = it.get("medicine_id") or it.get("id")
            qty = it.get("quantity") or it.get("qty") or 1
            if mid:
                try:
                    m_int = int(mid)
                    q_int = int(qty)
                    if m_int <= 0 or q_int <= 0:
                        return jsonify({"error": "Item medicine_id and quantity must be positive integers."}), 400
                    cart_items.append({"medicine_id": m_int, "quantity": q_int})
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid non-integer medicine_id or quantity in items payload."}), 400
        if not cart_items:
            return jsonify({"error": "No valid items in order payload."}), 400
        has_direct_items = True
    else:
        has_direct_items = False
        cart = query_db("SELECT * FROM carts WHERE user_id = ?", (user_id,), one=True)
        if not cart:
            return jsonify({"error": "Cart is empty."}), 400

        cart_items = query_db("SELECT medicine_id, quantity FROM cart_items WHERE cart_id = ?", (cart["id"],))
        if not cart_items:
            return jsonify({"error": "Your cart contains no items."}), 400

        pharmacy_id = cart["pharmacy_id"]
        if not pharmacy_id:
            return jsonify({"error": "No pharmacy is associated with this order."}), 400

    try:
        order = OrderService.create_order(
            customer_id=user_id,
            pharmacy_id=pharmacy_id,
            items=[dict(ci) for ci in cart_items],
            delivery_address=delivery_address,
            prescription_id=prescription_id,
            delivery_notes=delivery_notes
        )

        # Clear cart upon successful order placement if cart was used
        if not has_direct_items:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart["id"],))
            conn.commit()

        return jsonify({
            "status": "success",
            "message": "Order created successfully.",
            "order_id": order.get("id"),
            "order_number": order.get("id"),
            "total_amount": order.get("total_amount"),
            "order": order
        }), 201

    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to place order: {str(e)}"}), 500

@order_bp.route("", methods=["GET"])
@login_required
def list_orders():
    """
    Lists orders with strict role-based visibility filtering.
    """
    user_id = session["user_id"]
    role = session["role"]
    pharmacy_id = session.get("pharmacy_id")

    if role == "customer":
        orders = query_db("""
            SELECT o.*, p.name as pharmacy_name
            FROM orders o
            JOIN pharmacies p ON o.pharmacy_id = p.id
            WHERE o.customer_id = ?
            ORDER BY o.created_at DESC
        """, (user_id,))
    elif role == "pharmacy":
        if not pharmacy_id:
            return jsonify({"error": "User is not associated with an approved pharmacy."}), 403
        orders = query_db("""
            SELECT o.*, u.full_name as customer_name, u.phone as customer_phone
            FROM orders o
            JOIN users u ON o.customer_id = u.id
            WHERE o.pharmacy_id = ?
            ORDER BY o.created_at DESC
        """, (pharmacy_id,))
    elif role == "delivery":
        orders = query_db("""
            SELECT o.*, p.name as pharmacy_name, p.address as pharmacy_address
            FROM orders o
            JOIN pharmacies p ON o.pharmacy_id = p.id
            WHERE o.delivery_person_id = ?
            ORDER BY o.created_at DESC
        """, (user_id,))
    elif role == "admin":
        orders = query_db("""
            SELECT o.*, u.full_name as customer_name, p.name as pharmacy_name, d.full_name as delivery_name
            FROM orders o
            JOIN users u ON o.customer_id = u.id
            JOIN pharmacies p ON o.pharmacy_id = p.id
            LEFT JOIN users d ON o.delivery_person_id = d.id
            ORDER BY o.created_at DESC
        """)
    else:
        return jsonify({"error": "Unauthorized role."}), 403

    return jsonify({"status": "success", "orders": [format_order_response(o, user_id=user_id, role=role) for o in orders]})

@order_bp.route("/<string:order_id>", methods=["GET"])
@login_required
def get_order(order_id: str):
    """
    Fetches full authoritative order details, asserting access rights based on role.
    """
    user_id = session["user_id"]
    role = session["role"]
    pharmacy_id = session.get("pharmacy_id")

    order = OrderService.get_order_details(order_id)
    if not order:
        return jsonify({"error": f"Order '{order_id}' not found."}), 404

    # Authorization enforcement
    if role == "customer" and order["customer_id"] != user_id:
        return jsonify({"error": "Access denied. You do not own this order."}), 403
    elif role == "pharmacy" and order["pharmacy_id"] != pharmacy_id:
        return jsonify({"error": "Access denied. Order belongs to another pharmacy."}), 403
    elif role == "delivery" and order["delivery_person_id"] != user_id and order["order_status"] != "READY_FOR_PICKUP":
        return jsonify({"error": "Access denied. This delivery is not assigned to you."}), 403

    order_dict = dict(order)
    if role != "customer" or order_dict.get("customer_id") != user_id:
        order_dict["delivery_otp"] = None

    return jsonify({"status": "success", "order": order_dict})

@order_bp.route("/<string:order_id>/transition", methods=["POST"])
@login_required
def transition_status(order_id: str):
    data = request.get_json() or {}
    target_status = data.get("target_status")
    notes = data.get("notes")

    if not target_status:
        return jsonify({"error": "target_status is required."}), 400

    try:
        updated_order = OrderService.transition_order_status(
            order_id=order_id,
            target_status=target_status,
            user_id=session["user_id"],
            user_role=session["role"],
            notes=notes
        )
        return jsonify({
            "status": "success",
            "message": f"Order status transitioned to '{target_status}'.",
            "order": updated_order
        })
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Transition failed: {str(e)}"}), 500

@order_bp.route("/<string:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id: str):
    data = request.get_json() or {}
    reason = data.get("reason", "Cancelled by customer")

    try:
        updated_order = OrderService.transition_order_status(
            order_id=order_id,
            target_status="CANCELLED",
            user_id=session["user_id"],
            user_role=session["role"],
            notes=reason
        )
        return jsonify({
            "status": "success",
            "message": "Order has been cancelled.",
            "order": updated_order
        })
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Cancellation failed: {str(e)}"}), 500
