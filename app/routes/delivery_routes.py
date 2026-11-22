"""
Delivery Portal API Routes for MediApp.
Manages delivery personnel profile, available delivery pool, assignment claims,
and live delivery workflow transitions (Claim -> Picked Up -> In Transit -> Delivered).
"""
from flask import Blueprint, request, jsonify, session
import json
from datetime import datetime, timezone
from app.services.auth_service import login_required, roles_required
from app.services.order_service import OrderService
from app.database import query_db, get_db, transaction

delivery_bp = Blueprint("delivery", __name__, url_prefix="/api/delivery")

def check_delivery_authorization():
    if session.get("role") == "admin":
        return
    user_id = session.get("user_id")
    dp = query_db("SELECT status FROM delivery_profiles WHERE user_id = ?", (user_id,), one=True)
    if not dp:
        raise PermissionError("No delivery partner profile found for this user account.")
    if dp["status"] != "approved":
        raise PermissionError(f"Delivery partner account status is '{dp['status']}'. Must be 'approved' to claim and perform deliveries.")

@delivery_bp.route("/profile", methods=["GET"])
@login_required
@roles_required("delivery", "admin")
def get_delivery_profile():
    user_id = session["user_id"]
    profile = query_db("""
        SELECT u.id, u.full_name, u.email, u.phone, dp.*
        FROM users u
        LEFT JOIN delivery_profiles dp ON u.id = dp.user_id
        WHERE u.id = ?
    """, (user_id,), one=True)
    return jsonify({"status": "success", "profile": dict(profile) if profile else None})

@delivery_bp.route("/location", methods=["POST"])
@login_required
@roles_required("delivery", "admin")
def update_delivery_location():
    """Broadcasts rider GPS coordinates and updates live location in database."""
    try:
        check_delivery_authorization()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    user_id = session["user_id"]
    data = request.get_json() or {}
    lat = data.get("latitude")
    lon = data.get("longitude")

    if lat is None or lon is None:
        return jsonify({"error": "Both latitude and longitude are required."}), 400

    try:
        lat_f = float(lat)
        lon_f = float(lon)
        if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
            return jsonify({"error": "Coordinates out of bounds."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Coordinates must be valid numeric values."}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE delivery_profiles
        SET current_latitude = ?, current_longitude = ?
        WHERE user_id = ?
    """, (lat_f, lon_f, user_id))
    conn.commit()

    return jsonify({
        "status": "success",
        "message": "Delivery location updated.",
        "location": {"latitude": lat_f, "longitude": lon_f}
    })

@delivery_bp.route("/available", methods=["GET"])
@login_required
@roles_required("delivery", "admin")
def get_available_deliveries():
    """Returns orders ready for pickup that have not yet been assigned to a delivery person."""
    try:
        check_delivery_authorization()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    orders = query_db("""
        SELECT o.id, o.order_status, o.total_amount, o.delivery_fee, o.created_at,
               p.name as pharmacy_name, p.address as pharmacy_address, p.phone as pharmacy_phone,
               o.delivery_address_json,
               (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count
        FROM orders o
        JOIN pharmacies p ON o.pharmacy_id = p.id
        WHERE o.order_status = 'READY_FOR_PICKUP' AND o.delivery_person_id IS NULL
        ORDER BY o.created_at ASC
    """)
    order_list = []
    for row in orders:
        o = dict(row)
        addr_raw = o.get("delivery_address_json")
        delivery_addr = ""
        if addr_raw:
            try:
                parsed = json.loads(addr_raw)
                if isinstance(parsed, dict):
                    line1 = parsed.get("address_line1") or parsed.get("line1") or ""
                    line2 = parsed.get("address_line2") or parsed.get("line2") or ""
                    city = parsed.get("city") or ""
                    pincode = parsed.get("pincode") or parsed.get("postal_code") or ""
                    parts = [p for p in [line1, line2, city, pincode] if p]
                    delivery_addr = ", ".join(parts) if parts else str(parsed)
                elif isinstance(parsed, str):
                    delivery_addr = parsed.strip()
                else:
                    delivery_addr = str(parsed)
            except Exception:
                delivery_addr = str(addr_raw).strip('"')
        o["delivery_address"] = delivery_addr
        order_list.append(o)
    return jsonify({
        "status": "success",
        "orders": order_list,
        "available_orders": order_list
    })

@delivery_bp.route("/active", methods=["GET"])
@login_required
@roles_required("delivery", "admin")
def get_active_delivery():
    """Returns the delivery currently assigned to and being fulfilled by this user."""
    user_id = session["user_id"]
    order = query_db("""
        SELECT o.*,
               u.full_name as customer_name, u.phone as customer_phone,
               p.name as pharmacy_name, p.address as pharmacy_address, p.phone as pharmacy_phone,
               da.pickup_time, da.status as assignment_status
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        JOIN pharmacies p ON o.pharmacy_id = p.id
        JOIN delivery_assignments da ON o.id = da.order_id
        WHERE o.delivery_person_id = ?
          AND o.order_status IN ('DELIVERY_ASSIGNED', 'PICKED_UP', 'IN_TRANSIT')
        ORDER BY o.created_at DESC
        LIMIT 1
    """, (user_id,), one=True)

    if not order:
        return jsonify({"status": "success", "active_order": None})

    order_details = OrderService.get_order_details(order["id"], user_role=session.get("role"))
    if session.get("role") == "delivery" and order_details:
        order_details["delivery_otp"] = None
    return jsonify({"status": "success", "active_order": order_details})

@delivery_bp.route("/orders/<string:order_id>/claim", methods=["POST"])
@delivery_bp.route("/orders/<string:order_id>/accept", methods=["POST"])
@login_required
@roles_required("delivery", "admin")
def claim_delivery(order_id: str):
    """Atomically claims an order from the available pool."""
    try:
        check_delivery_authorization()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    user_id = session["user_id"]
    conn = get_db()
    with transaction(conn):
        cur = conn.cursor()
        
        # Check order state and ensure it's unassigned
        order = query_db("SELECT * FROM orders WHERE id = ?", (order_id,), one=True, conn=conn)
        if not order:
            return jsonify({"error": f"Order '{order_id}' not found."}), 404

        # Ensure rider does not exceed active courier batch capacity (max 5 active deliveries)
        active_count_row = query_db("""
            SELECT COUNT(*) as c FROM orders 
            WHERE delivery_person_id = ? AND order_status IN ('DELIVERY_ASSIGNED', 'PICKED_UP', 'IN_TRANSIT')
        """, (user_id,), one=True, conn=conn)
        if active_count_row and active_count_row["c"] >= 5:
            return jsonify({
                "error": "You have reached the maximum active delivery capacity (5 orders). Complete existing deliveries before claiming more."
            }), 409

        if order["delivery_person_id"] is not None:
            return jsonify({"error": "This delivery has already been claimed by another rider."}), 409
        if order["order_status"] != "READY_FOR_PICKUP":
            return jsonify({"error": f"Order cannot be claimed in status '{order['order_status']}'."}), 400

        # Assign order to delivery person and update status to DELIVERY_ASSIGNED atomically
        cur.execute("""
            UPDATE orders
            SET delivery_person_id = ?, order_status = 'DELIVERY_ASSIGNED', updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND delivery_person_id IS NULL AND order_status = 'READY_FOR_PICKUP'
        """, (user_id, order_id))

        if cur.rowcount == 0:
            return jsonify({"error": "This delivery has already been claimed by another rider."}), 409

        # Create or update delivery assignment
        cur.execute("""
            INSERT INTO delivery_assignments (order_id, delivery_person_id, status)
            VALUES (?, ?, 'assigned')
            ON CONFLICT(order_id) DO UPDATE SET
                delivery_person_id = excluded.delivery_person_id,
                status = 'assigned'
        """, (order_id, user_id))

        # Record status history
        cur.execute("""
            INSERT INTO order_status_history (order_id, from_status, to_status, changed_by_user_id, role, notes)
            VALUES (?, 'READY_FOR_PICKUP', 'DELIVERY_ASSIGNED', ?, 'delivery', 'Claimed by delivery personnel')
        """, (order_id, user_id))

    updated_order = OrderService.get_order_details(order_id, user_role=session.get("role"))
    if session.get("role") == "delivery" and updated_order:
        updated_order["delivery_otp"] = None
    return jsonify({"status": "success", "message": "Delivery successfully claimed.", "order": updated_order})

@delivery_bp.route("/orders/<string:order_id>/pickup", methods=["POST"])
@login_required
@roles_required("delivery", "admin")
def pickup_order(order_id: str):
    try:
        check_delivery_authorization()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    user_id = session["user_id"]
    try:
        conn = get_db()
        with transaction(conn):
            cur = conn.cursor()
            cur.execute("""
                UPDATE delivery_assignments
                SET status = 'picked_up', pickup_time = CURRENT_TIMESTAMP
                WHERE order_id = ? AND delivery_person_id = ?
            """, (order_id, user_id))
            
            OrderService.transition_order_status(
                order_id=order_id,
                target_status="PICKED_UP",
                user_id=user_id,
                user_role="delivery",
                notes="Package collected from pharmacy",
                conn=conn
            )
        return jsonify({"status": "success", "message": "Order marked as picked up."})
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@delivery_bp.route("/orders/<string:order_id>/in-transit", methods=["POST"])
@login_required
@roles_required("delivery", "admin")
def mark_in_transit(order_id: str):
    try:
        check_delivery_authorization()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    user_id = session["user_id"]
    try:
        conn = get_db()
        with transaction(conn):
            cur = conn.cursor()
            cur.execute("""
                UPDATE delivery_assignments
                SET status = 'in_transit'
                WHERE order_id = ? AND delivery_person_id = ?
            """, (order_id, user_id))
            
            OrderService.transition_order_status(
                order_id=order_id,
                target_status="IN_TRANSIT",
                user_id=user_id,
                user_role="delivery",
                notes="Rider is en route to delivery address",
                conn=conn
            )
        return jsonify({"status": "success", "message": "Order marked in transit."})
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@delivery_bp.route("/orders/<string:order_id>/complete", methods=["POST"])
@delivery_bp.route("/orders/<string:order_id>/verify-otp", methods=["POST"])
@login_required
@roles_required("delivery", "admin")
def complete_delivery(order_id: str):
    try:
        check_delivery_authorization()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    user_id = session["user_id"]
    data = request.get_json() or {}
    otp = data.get("otp")

    order = query_db("SELECT delivery_otp, order_status FROM orders WHERE id = ?", (order_id,), one=True)
    if not order:
        return jsonify({"error": f"Order {order_id} not found."}), 404

    expected_otp = str(order["delivery_otp"] or "").strip()
    if expected_otp and otp:
        if str(otp).strip() != expected_otp:
            return jsonify({"error": "Invalid delivery OTP. Handover cannot be completed without correct patient verification."}), 400
    elif not otp and not data.get("proof"):
        return jsonify({"error": "Patient delivery OTP is required to complete handover."}), 400

    proof = data.get("proof") or f"Patient OTP handoff verified: {otp}"

    try:
        conn = get_db()
        with transaction(conn):
            cur = conn.cursor()
            cur.execute("""
                UPDATE delivery_assignments
                SET status = 'delivered', delivery_time = CURRENT_TIMESTAMP, proof_of_delivery = ?
                WHERE order_id = ? AND delivery_person_id = ?
            """, (proof, order_id, user_id))
            
            OrderService.transition_order_status(
                order_id=order_id,
                target_status="DELIVERED",
                user_id=user_id,
                user_role="delivery",
                notes=f"Delivery completed: {proof}",
                conn=conn
            )
        return jsonify({"status": "success", "message": "Order marked as successfully delivered."})
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@delivery_bp.route("/orders/<string:order_id>/fail", methods=["POST"])
@login_required
@roles_required("delivery", "admin")
def fail_delivery(order_id: str):
    try:
        check_delivery_authorization()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    user_id = session["user_id"]
    data = request.get_json() or {}
    reason = data.get("reason", "Customer unavailable / Address unreachable")

    try:
        conn = get_db()
        with transaction(conn):
            cur = conn.cursor()
            cur.execute("""
                UPDATE delivery_assignments
                SET status = 'failed', failure_reason = ?
                WHERE order_id = ? AND delivery_person_id = ?
            """, (reason, order_id, user_id))
            
            OrderService.transition_order_status(
                order_id=order_id,
                target_status="DELIVERY_FAILED",
                user_id=user_id,
                user_role="delivery",
                notes=f"Delivery failed attempt: {reason}",
                conn=conn
            )
        return jsonify({"status": "success", "message": "Order status updated to delivery failed."})
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@delivery_bp.route("/history", methods=["GET"])
@login_required
@roles_required("delivery", "admin")
def get_delivery_history():
    user_id = session["user_id"]
    orders = query_db("""
        SELECT o.id, o.total_amount, o.delivery_fee, o.created_at, o.order_status,
               p.name as pharmacy_name, da.delivery_time, da.proof_of_delivery, da.failure_reason
        FROM orders o
        JOIN pharmacies p ON o.pharmacy_id = p.id
        JOIN delivery_assignments da ON o.id = da.order_id
        WHERE o.delivery_person_id = ?
        ORDER BY o.created_at DESC
        LIMIT 30
    """, (user_id,))
    return jsonify({"status": "success", "history": [dict(o) for o in orders]})
