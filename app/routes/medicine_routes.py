"""
Medicine Catalogue & Clinical Discovery Routes for MediApp.
Supports debounced search, filtering by category/form/Rx, pharmacy-specific stock,
Drug-Drug Interaction screening, and generic alternatives.
"""
from flask import Blueprint, request, jsonify
from app.database import query_db
from app.services.ddi_service import DDIService

medicine_bp = Blueprint("medicines", __name__, url_prefix="/api/medicines")

@medicine_bp.route("", methods=["GET"])
def search_medicines():
    """
    Search and filter medicine catalogue with pagination.
    Query params: q, category, dosage_form, rx, pharmacy_id, page, limit
    """
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    dosage_form = request.args.get("dosage_form", "").strip()
    rx = request.args.get("rx")
    pharmacy_id = request.args.get("pharmacy_id", type=int)
    
    page = max(1, request.args.get("page", 1, type=int))
    limit = min(100, max(1, request.args.get("limit", 20, type=int)))
    offset = (page - 1) * limit

    conditions = []
    params = []

    if q:
        search_pattern = f"%{q}%"
        conditions.append("(m.name LIKE ? OR m.generic_name LIKE ? OR m.category LIKE ? OR m.uses LIKE ?)")
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    if category:
        conditions.append("m.category = ?")
        params.append(category)

    if dosage_form:
        conditions.append("m.dosage_form = ?")
        params.append(dosage_form)

    if rx is not None and rx != "":
        conditions.append("m.prescription_required = ?")
        params.append(int(rx))

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    if pharmacy_id:
        sql = f"""
            SELECT m.*,
                   COALESCE(i.stock_quantity, 0) as stock_quantity,
                   COALESCE(i.unit_price, m.mrp) as unit_price,
                   COALESCE(i.is_available, 0) as is_available
            FROM medicines m
            LEFT JOIN pharmacy_inventory i ON m.id = i.medicine_id AND i.pharmacy_id = ?
            {where_clause}
            ORDER BY m.name ASC
            LIMIT ? OFFSET ?
        """
        full_params = [pharmacy_id] + params + [limit, offset]
        
        count_sql = f"""
            SELECT COUNT(*) as cnt
            FROM medicines m
            LEFT JOIN pharmacy_inventory i ON m.id = i.medicine_id AND i.pharmacy_id = ?
            {where_clause}
        """
        count_params = [pharmacy_id] + params
    else:
        sql = f"""
            SELECT m.*
            FROM medicines m
            {where_clause}
            ORDER BY m.name ASC
            LIMIT ? OFFSET ?
        """
        full_params = params + [limit, offset]
        
        count_sql = f"SELECT COUNT(*) as cnt FROM medicines m {where_clause}"
        count_params = params

    items = query_db(sql, full_params)
    total_row = query_db(count_sql, count_params, one=True)
    total_count = total_row["cnt"] if total_row else 0

    return jsonify({
        "status": "success",
        "medicines": [dict(it) for it in items],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit
        }
    })

@medicine_bp.route("/<int:med_id>", methods=["GET"])
def get_medicine_detail(med_id: int):
    pharmacy_id = request.args.get("pharmacy_id", type=int)
    
    if pharmacy_id:
        med = query_db("""
            SELECT m.*,
                   COALESCE(i.stock_quantity, 0) as stock_quantity,
                   COALESCE(i.unit_price, m.mrp) as unit_price,
                   COALESCE(i.is_available, 0) as is_available,
                   p.name as pharmacy_name
            FROM medicines m
            LEFT JOIN pharmacy_inventory i ON m.id = i.medicine_id AND i.pharmacy_id = ?
            LEFT JOIN pharmacies p ON p.id = ?
            WHERE m.id = ?
        """, (pharmacy_id, pharmacy_id, med_id), one=True)
    else:
        med = query_db("SELECT * FROM medicines WHERE id = ?", (med_id,), one=True)

    if not med:
        return jsonify({"error": f"Medicine ID {med_id} not found."}), 404

    return jsonify({"status": "success", "medicine": dict(med)})

@medicine_bp.route("/categories", methods=["GET"])
def get_categories():
    rows = query_db("""
        SELECT category, COUNT(*) as count
        FROM medicines
        GROUP BY category
        ORDER BY count DESC
    """)
    return jsonify({"status": "success", "categories": [dict(r) for r in rows]})

@medicine_bp.route("/dosage-forms", methods=["GET"])
def get_dosage_forms():
    rows = query_db("""
        SELECT DISTINCT dosage_form
        FROM medicines
        ORDER BY dosage_form ASC
    """)
    return jsonify({"status": "success", "dosage_forms": [r["dosage_form"] for r in rows]})

@medicine_bp.route("/check-ddi", methods=["POST"])
def check_ddi():
    """Analyzes a list of medicine IDs for clinical drug interactions."""
    data = request.get_json() or {}
    med_ids = data.get("medicine_ids", [])
    
    if not med_ids:
        return jsonify({"has_interactions": False, "interactions": []})

    placeholders = ",".join(["?"] * len(med_ids))
    meds = query_db(f"SELECT id, name, generic_name FROM medicines WHERE id IN ({placeholders})", med_ids)
    
    analysis = DDIService.check_interactions_for_medicines(meds)
    return jsonify(analysis)

@medicine_bp.route("/<int:med_id>/generic-alternatives", methods=["GET"])
def get_generic_alternatives(med_id: int):
    """Returns lower-cost bioequivalent generic options for a target medicine."""
    result = DDIService.get_generic_alternatives(med_id)
    return jsonify(result)
