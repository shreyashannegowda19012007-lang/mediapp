"""
Pharmacy / Shop Portal API Routes for MediApp.
Provides live dashboard metrics, order acceptance and fulfilment workflow,
and inventory stock and price management.
"""
from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required, roles_required
from app.services.order_service import OrderService
from app.services.inventory_service import InventoryService
from app.database import query_db, get_db

pharmacy_bp = Blueprint("pharmacy", __name__, url_prefix="/api/pharmacy")

def get_current_pharmacy_id() -> int:
    pharm_id = session.get("pharmacy_id")
    if not pharm_id and session.get("role") == "admin":
        pharm_id = request.args.get("pharmacy_id", type=int) or 1
    if not pharm_id:
        raise PermissionError("User is not associated with an approved pharmacy.")
    pharm = query_db("SELECT status, name FROM pharmacies WHERE id = ?", (pharm_id,), one=True)
    if not pharm:
        raise PermissionError("Associated pharmacy not found.")
    if session.get("role") != "admin" and pharm["status"] != "approved":
        raise PermissionError(f"Pharmacy '{pharm['name']}' is {pharm['status']} and cannot perform operational duties.")
    return pharm_id

@pharmacy_bp.route("/dashboard", methods=["GET"])
@login_required
@roles_required("pharmacy", "admin")
def get_dashboard_metrics():
    """Calculates live operational metrics from real database records."""
    try:
        pharmacy_id = get_current_pharmacy_id()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    pharmacy = query_db("SELECT * FROM pharmacies WHERE id = ?", (pharmacy_id,), one=True)
    if not pharmacy:
        return jsonify({"error": "Pharmacy record not found."}), 404

    # Order counts by status
    status_counts = query_db("""
        SELECT order_status, COUNT(*) as count
        FROM orders
        WHERE pharmacy_id = ?
        GROUP BY order_status
    """, (pharmacy_id,))
    status_map = {r["order_status"]: r["count"] for r in status_counts}

    # Revenue calculation from completed orders
    rev_row = query_db("""
        SELECT COALESCE(SUM(total_amount), 0.0) as total_revenue
        FROM orders
        WHERE pharmacy_id = ? AND payment_status = 'paid' AND order_status = 'DELIVERED'
    """, (pharmacy_id,), one=True)
    revenue = rev_row["total_revenue"] if rev_row else 0.0

    # Low-stock alerts
    low_stock = query_db("""
        SELECT COUNT(*) as count
        FROM pharmacy_inventory
        WHERE pharmacy_id = ? AND stock_quantity <= low_stock_threshold
    """, (pharmacy_id,), one=True)

    # Active pending queue
    pending_orders = query_db("""
        SELECT o.*, u.full_name as customer_name, u.phone as customer_phone
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        WHERE o.pharmacy_id = ? AND o.order_status IN ('PLACED', 'AWAITING_PRESCRIPTION', 'PRESCRIPTION_VERIFIED', 'ACCEPTED', 'PREPARING')
        ORDER BY o.created_at DESC
        LIMIT 10
    """, (pharmacy_id,))

    return jsonify({
        "status": "success",
        "pharmacy": dict(pharmacy),
        "metrics": {
            "new_orders": status_map.get("PLACED", 0) + status_map.get("AWAITING_PRESCRIPTION", 0),
            "prescription_review": status_map.get("AWAITING_PRESCRIPTION", 0),
            "accepted_orders": status_map.get("ACCEPTED", 0),
            "preparing_orders": status_map.get("PREPARING", 0),
            "ready_for_pickup": status_map.get("READY_FOR_PICKUP", 0),
            "delivered_orders": status_map.get("DELIVERED", 0),
            "cancelled_orders": status_map.get("CANCELLED", 0),
            "total_revenue": round(float(revenue), 2),
            "low_stock_alerts": low_stock["count"] if low_stock else 0
        },
        "active_queue": [dict(o) for o in pending_orders]
    })

@pharmacy_bp.route("/orders", methods=["GET"])
@login_required
@roles_required("pharmacy", "admin")
def list_pharmacy_orders():
    try:
        pharmacy_id = get_current_pharmacy_id()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    status_filter = request.args.get("status")
    if status_filter:
        orders = query_db("""
            SELECT o.*, u.full_name as customer_name, u.phone as customer_phone
            FROM orders o
            JOIN users u ON o.customer_id = u.id
            WHERE o.pharmacy_id = ? AND o.order_status = ?
            ORDER BY o.created_at DESC
        """, (pharmacy_id, status_filter))
    else:
        orders = query_db("""
            SELECT o.*, u.full_name as customer_name, u.phone as customer_phone
            FROM orders o
            JOIN users u ON o.customer_id = u.id
            WHERE o.pharmacy_id = ?
            ORDER BY o.created_at DESC
        """, (pharmacy_id,))

    return jsonify({"status": "success", "orders": [dict(o) for o in orders]})

@pharmacy_bp.route("/orders/<string:order_id>/accept", methods=["POST"])
@login_required
@roles_required("pharmacy", "admin")
def accept_order(order_id: str):
    try:
        pharmacy_id = get_current_pharmacy_id()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    order = query_db("SELECT pharmacy_id FROM orders WHERE id = ?", (order_id,), one=True)
    if not order:
        return jsonify({"error": f"Order '{order_id}' not found."}), 404
    if session.get("role") != "admin" and order["pharmacy_id"] != pharmacy_id:
        return jsonify({"error": "Access denied. Order belongs to another pharmacy store."}), 403

    try:
        updated = OrderService.transition_order_status(
            order_id=order_id,
            target_status="ACCEPTED",
            user_id=session["user_id"],
            user_role=session["role"],
            notes="Order accepted by pharmacy"
        )
        return jsonify({"status": "success", "message": "Order accepted.", "order": updated})
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@pharmacy_bp.route("/orders/<string:order_id>/reject", methods=["POST"])
@login_required
@roles_required("pharmacy", "admin")
def reject_order(order_id: str):
    try:
        pharmacy_id = get_current_pharmacy_id()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    order = query_db("SELECT pharmacy_id FROM orders WHERE id = ?", (order_id,), one=True)
    if not order:
        return jsonify({"error": f"Order '{order_id}' not found."}), 404
    if session.get("role") != "admin" and order["pharmacy_id"] != pharmacy_id:
        return jsonify({"error": "Access denied. Order belongs to another pharmacy store."}), 403

    data = request.get_json() or {}
    reason = data.get("reason", "Rejected by pharmacy")
    try:
        updated = OrderService.transition_order_status(
            order_id=order_id,
            target_status="CANCELLED",
            user_id=session["user_id"],
            user_role=session["role"],
            notes=f"Pharmacy rejected: {reason}"
        )
        return jsonify({"status": "success", "message": "Order rejected and cancelled.", "order": updated})
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@pharmacy_bp.route("/inventory", methods=["GET"])
@login_required
@roles_required("pharmacy", "admin")
def get_inventory():
    try:
        pharmacy_id = get_current_pharmacy_id()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    q = request.args.get("q", "").strip()
    low_stock_only = request.args.get("low_stock", type=bool)
    page = max(1, request.args.get("page", 1, type=int))
    limit = min(100, max(1, request.args.get("limit", 25, type=int)))
    offset = (page - 1) * limit

    conditions = ["pi.pharmacy_id = ?"]
    params = [pharmacy_id]

    if q:
        conditions.append("(m.name LIKE ? OR m.generic_name LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])

    if low_stock_only:
        conditions.append("pi.stock_quantity <= pi.low_stock_threshold")

    where_sql = f"WHERE {' AND '.join(conditions)}"

    items = query_db(f"""
        SELECT pi.*, m.name, m.generic_name, m.strength, m.dosage_form, m.category, m.mrp, m.prescription_required
        FROM pharmacy_inventory pi
        JOIN medicines m ON pi.medicine_id = m.id
        {where_sql}
        ORDER BY pi.stock_quantity ASC, m.name ASC
        LIMIT ? OFFSET ?
    """, params + [limit, offset])

    count_row = query_db(f"""
        SELECT COUNT(*) as cnt
        FROM pharmacy_inventory pi
        JOIN medicines m ON pi.medicine_id = m.id
        {where_sql}
    """, params, one=True)
    total_count = count_row["cnt"] if count_row else 0

    return jsonify({
        "status": "success",
        "inventory": [dict(it) for it in items],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit
        }
    })

@pharmacy_bp.route("/inventory", methods=["POST"])
@login_required
@roles_required("pharmacy", "admin")
def add_inventory_item():
    try:
        pharmacy_id = get_current_pharmacy_id()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    data = request.get_json() or {}
    medicine_id = data.get("medicine_id")
    quantity = data.get("quantity")
    unit_price = data.get("unit_price")
    batch_number = data.get("batch_number")
    expiry_date = data.get("expiry_date")
    is_available = data.get("is_available", True)

    if not medicine_id or quantity is None or unit_price is None:
        return jsonify({"error": "medicine_id, quantity, and unit_price are required."}), 400

    try:
        InventoryService.update_stock(
            pharmacy_id=pharmacy_id,
            medicine_id=medicine_id,
            quantity=int(quantity),
            unit_price=float(unit_price),
            is_available=bool(is_available),
            batch_number=batch_number,
            expiry_date=expiry_date
        )
        return jsonify({"status": "success", "message": "Inventory saved successfully."})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@pharmacy_bp.route("/inventory/<int:medicine_id>", methods=["PUT"])
@login_required
@roles_required("pharmacy", "admin")
def update_inventory_item(medicine_id: int):
    try:
        pharmacy_id = get_current_pharmacy_id()
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    data = request.get_json() or {}
    quantity = data.get("quantity")
    unit_price = data.get("unit_price")
    is_available = data.get("is_available")

    current = query_db("""
        SELECT * FROM pharmacy_inventory WHERE pharmacy_id = ? AND medicine_id = ?
    """, (pharmacy_id, medicine_id), one=True)
    if not current:
        return jsonify({"error": "Inventory record not found."}), 404

    qty = int(quantity) if quantity is not None else current["stock_quantity"]
    prc = float(unit_price) if unit_price is not None else current["unit_price"]
    avail = bool(is_available) if is_available is not None else bool(current["is_available"])

    try:
        InventoryService.update_stock(
            pharmacy_id=pharmacy_id,
            medicine_id=medicine_id,
            quantity=qty,
            unit_price=prc,
            is_available=avail,
            batch_number=data.get("batch_number", current["batch_number"]),
            expiry_date=data.get("expiry_date", current["expiry_date"])
        )
        return jsonify({"status": "success", "message": "Stock record updated."})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
