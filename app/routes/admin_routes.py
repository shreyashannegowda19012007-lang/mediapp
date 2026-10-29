"""
Administrator Portal API Routes for MediApp.
Provides system-wide analytics, user and pharmacy management,
catalogue oversight, orders auditing, and diagnostic health checks.
"""
from flask import Blueprint, request, jsonify, session
from app.services.auth_service import login_required, roles_required
from app.config import Config
from app.database import query_db, get_db

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@admin_bp.route("/stats", methods=["GET"])
@login_required
@roles_required("admin")
def get_system_stats():
    """
    Computes global platform analytics from live database tables.
    Guaranteed not to crash on empty tables.
    """
    # 1. Total revenue
    rev_row = query_db("""
        SELECT COALESCE(SUM(total_amount), 0.0) as rev
        FROM orders
        WHERE payment_status = 'paid'
    """, one=True)
    total_revenue = round(float(rev_row["rev"]), 2) if rev_row else 0.0

    # 2. Total orders and breakdown
    status_rows = query_db("SELECT order_status, COUNT(*) as c FROM orders GROUP BY order_status")
    status_dist = {r["order_status"]: r["c"] for r in status_rows}
    total_orders = sum(status_dist.values())

    # 3. User distribution
    user_rows = query_db("SELECT role, COUNT(*) as c FROM users GROUP BY role")
    user_dist = {r["role"]: r["c"] for r in user_rows}
    total_users = sum(user_dist.values())

    # 4. Pharmacy statistics
    pharm_rows = query_db("SELECT status, COUNT(*) as c FROM pharmacies GROUP BY status")
    pharm_dist = {r["status"]: r["c"] for r in pharm_rows}
    total_pharmacies = sum(pharm_dist.values())

    # 5. Inventory and Catalogue metrics
    med_count_row = query_db("SELECT COUNT(*) as c FROM medicines", one=True)
    total_catalogue = med_count_row["c"] if med_count_row else 0

    low_stock_row = query_db("SELECT COUNT(*) as c FROM pharmacy_inventory WHERE stock_quantity <= low_stock_threshold", one=True)
    low_stock_count = low_stock_row["c"] if low_stock_row else 0

    # Recent 8 orders
    recent_orders = query_db("""
        SELECT o.id, o.total_amount, o.order_status, o.payment_status, o.created_at,
               u.full_name as customer_name, p.name as pharmacy_name
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        JOIN pharmacies p ON o.pharmacy_id = p.id
        ORDER BY o.created_at DESC
        LIMIT 8
    """)

    return jsonify({
        "status": "success",
        "metrics": {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "order_breakdown": status_dist,
            "total_users": total_users,
            "user_breakdown": user_dist,
            "total_pharmacies": total_pharmacies,
            "pharmacy_breakdown": pharm_dist,
            "total_catalogue_medicines": total_catalogue,
            "low_stock_alerts": low_stock_count
        },
        "recent_orders": [dict(o) for o in recent_orders]
    })

@admin_bp.route("/users", methods=["GET"])
@login_required
@roles_required("admin")
def list_users():
    role_filter = request.args.get("role")
    q = request.args.get("q", "").strip()

    conditions = []
    params = []
    if role_filter:
        conditions.append("role = ?")
        params.append(role_filter)
    if q:
        conditions.append("(email LIKE ? OR full_name LIKE ? OR phone LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    users = query_db(f"""
        SELECT id, email, full_name, phone, role, is_active, google_id, created_at
        FROM users
        {where_sql}
        ORDER BY id DESC
    """, params)

    return jsonify({"status": "success", "users": [dict(u) for u in users]})

@admin_bp.route("/users/<int:user_id>/status", methods=["PUT"])
@login_required
@roles_required("admin")
def toggle_user_status(user_id: int):
    data = request.get_json() or {}
    is_active = 1 if data.get("is_active", True) else 0

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (is_active, user_id))
    conn.commit()
    return jsonify({"status": "success", "message": "User status updated."})

@admin_bp.route("/pharmacies", methods=["GET"])
@login_required
@roles_required("admin")
def list_pharmacies():
    status_filter = request.args.get("status")
    if status_filter:
        pharmacies = query_db("SELECT * FROM pharmacies WHERE status = ? ORDER BY id DESC", (status_filter,))
    else:
        pharmacies = query_db("SELECT * FROM pharmacies ORDER BY id DESC")
    return jsonify({"status": "success", "pharmacies": [dict(p) for p in pharmacies]})

@admin_bp.route("/pharmacies/<int:pharmacy_id>/status", methods=["PUT"])
@login_required
@roles_required("admin")
def update_pharmacy_status(pharmacy_id: int):
    data = request.get_json() or {}
    new_status = data.get("status")
    if new_status not in ("pending", "approved", "suspended", "rejected"):
        return jsonify({"error": "Invalid status value."}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE pharmacies SET status = ? WHERE id = ?", (new_status, pharmacy_id))
    conn.commit()
    return jsonify({"status": "success", "message": f"Pharmacy status changed to {new_status}."})

@admin_bp.route("/audit-logs", methods=["GET"])
@login_required
@roles_required("admin")
def get_audit_logs():
    logs = query_db("""
        SELECT h.*, u.full_name as user_name
        FROM order_status_history h
        LEFT JOIN users u ON h.changed_by_user_id = u.id
        ORDER BY h.id DESC
        LIMIT 50
    """)
    return jsonify({"status": "success", "logs": [dict(l) for l in logs]})

@admin_bp.route("/system-health", methods=["GET"])
@login_required
@roles_required("admin")
def get_system_health():
    config_issues = Config.validate_config()
    db_test = query_db("SELECT 1 as ok", one=True)
    return jsonify({
        "status": "healthy" if not config_issues else "degraded",
        "database_connected": bool(db_test and db_test["ok"] == 1),
        "database_ready": bool(db_test and db_test["ok"] == 1),
        "app_env": Config.APP_ENV,
        "app_mode": Config.APP_MODE,
        "config_validation": {
            "is_valid": len(config_issues) == 0,
            "issues": config_issues
        },
        "capabilities": Config.get_public_capabilities()
    })
