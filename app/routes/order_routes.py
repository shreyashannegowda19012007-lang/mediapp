"""
Order Management Routes for MediApp.
Operates as the single authoritative order gateway shared across Customer,
Pharmacy, Delivery, and Admin portals.
"""
from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required
from app.services.order_service import OrderService
from app.database import query_db, get_db

order_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

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
    delivery_address = data.get("delivery_address")
    prescription_id = data.get("prescription_id")
    delivery_notes = data.get("delivery_notes")

    if not delivery_address:
        return jsonify({"error": "Delivery address is required."}), 400

    # Retrieve items from user's current cart
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

        # Clear cart upon successful order placement
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart["id"],))
        conn.commit()

        return jsonify({
            "status": "success",
            "message": "Order created successfully.",
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

    return jsonify({"status": "success", "orders": [dict(o) for o in orders]})

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

    return jsonify({"status": "success", "order": order})

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
    except (ValueError, PermissionError) as e:
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
    except (ValueError, PermissionError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Cancellation failed: {str(e)}"}), 500
