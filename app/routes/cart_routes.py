"""
Customer Cart API Routes for MediApp.
Handles server-persisted cart state, item additions, quantity updates,
real-time stock revalidation, and authoritative pricing calculation.
"""
from flask import Blueprint, request, jsonify, session
from app.database import get_db, query_db
from app.services.auth_service import login_required
from app.services.pricing_service import PricingService
from app.services.ddi_service import DDIService

cart_bp = Blueprint("cart", __name__, url_prefix="/api/cart")

def get_or_create_cart(user_id: int, pharmacy_id: int | None = None, clear_if_different: bool = False) -> dict:
    """Retrieves or creates user cart, managing pharmacy association and item isolation."""
    conn = get_db()
    cur = conn.cursor()
    cart = query_db("SELECT * FROM carts WHERE user_id = ?", (user_id,), one=True)
    
    if not cart:
        # Default to first approved pharmacy if none specified
        if not pharmacy_id:
            first_pharm = query_db("SELECT id FROM pharmacies WHERE status = 'approved' LIMIT 1", one=True)
            pharmacy_id = first_pharm["id"] if first_pharm else 1
            
        cur.execute("INSERT INTO carts (user_id, pharmacy_id) VALUES (?, ?)", (user_id, pharmacy_id))
        conn.commit()
        cart = query_db("SELECT * FROM carts WHERE id = ?", (cur.lastrowid,), one=True)
    elif pharmacy_id and cart["pharmacy_id"] != pharmacy_id:
        # Check if cart has existing items
        item_count_row = query_db("SELECT COUNT(*) as c FROM cart_items WHERE cart_id = ?", (cart["id"],), one=True)
        has_items = (item_count_row["c"] > 0) if item_count_row else False

        if has_items and not clear_if_different:
            cur_pharm = query_db("SELECT name FROM pharmacies WHERE id = ?", (cart["pharmacy_id"],), one=True)
            new_pharm = query_db("SELECT name FROM pharmacies WHERE id = ?", (pharmacy_id,), one=True)
            raise ValueError(f"CROSS_PHARMACY_CONFLICT:{cur_pharm['name'] if cur_pharm else 'another pharmacy'}:{new_pharm['name'] if new_pharm else 'the selected pharmacy'}")

        if clear_if_different:
            cur.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart["id"],))

        cur.execute("UPDATE carts SET pharmacy_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (pharmacy_id, cart["id"]))
        conn.commit()
        cart = query_db("SELECT * FROM carts WHERE id = ?", (cart["id"],), one=True)
        
    return dict(cart)

@cart_bp.route("", methods=["GET"])
@login_required
def get_cart():
    user_id = session["user_id"]
    cart = get_or_create_cart(user_id)
    pharmacy_id = cart["pharmacy_id"]

    # Fetch enriched items
    items = query_db("""
        SELECT ci.id as cart_item_id, ci.medicine_id, ci.quantity,
               m.name, m.generic_name, m.strength, m.dosage_form, m.category,
               m.prescription_required, m.mrp,
               COALESCE(pi.unit_price, m.mrp) as unit_price,
               COALESCE(pi.stock_quantity, 0) as stock_quantity,
               COALESCE(pi.is_available, 0) as is_available
        FROM cart_items ci
        JOIN medicines m ON ci.medicine_id = m.id
        LEFT JOIN pharmacy_inventory pi ON ci.medicine_id = pi.medicine_id AND pi.pharmacy_id = ?
        WHERE ci.cart_id = ?
        ORDER BY ci.id ASC
    """, (pharmacy_id, cart["id"]))

    items_list = []
    has_rx_required = False
    has_out_of_stock = False
    
    for it in items:
        item_dict = dict(it)
        line_total = PricingService.calculate_item_total(item_dict["unit_price"], item_dict["quantity"])
        item_dict["line_total"] = float(line_total)
        
        if item_dict["prescription_required"]:
            has_rx_required = True
        if item_dict["stock_quantity"] < item_dict["quantity"] or not item_dict["is_available"]:
            has_out_of_stock = True
            item_dict["stock_warning"] = "Insufficient stock at selected pharmacy."
            
        items_list.append(item_dict)

    # Authoritative financial summary
    totals = PricingService.calculate_order_totals(items_list)

    # Check for clinical interactions between cart medicines
    med_objects = [{"id": it["medicine_id"], "name": it["name"], "generic_name": it["generic_name"]} for it in items_list]
    ddi_result = DDIService.check_interactions_for_medicines(med_objects) if len(med_objects) > 1 else {"has_interactions": False, "interactions": []}

    pharmacy = query_db("SELECT id, name, address, phone FROM pharmacies WHERE id = ?", (pharmacy_id,), one=True)

    return jsonify({
        "status": "success",
        "cart_id": cart["id"],
        "pharmacy_id": pharmacy_id,
        "pharmacy_name": pharmacy["name"] if pharmacy else "Apollo Clinical Hub (Central)",
        "pharmacy": dict(pharmacy) if pharmacy else None,
        "items": items_list,
        "item_count": sum(it["quantity"] for it in items_list),
        "totals": totals,
        "pricing": totals,
        "has_rx_required": has_rx_required,
        "has_prescription_items": has_rx_required,
        "has_out_of_stock": has_out_of_stock,
        "drug_interactions": ddi_result
    })

@cart_bp.route("/items", methods=["POST"])
@login_required
def add_to_cart():
    data = request.get_json() or {}
    medicine_id = data.get("medicine_id")
    quantity = data.get("quantity", 1)
    pharmacy_id = data.get("pharmacy_id")
    clear_existing = data.get("clear_existing", False)

    if not medicine_id or quantity <= 0:
        return jsonify({"error": "Valid medicine_id and quantity > 0 are required."}), 400

    user_id = session["user_id"]
    try:
        cart = get_or_create_cart(user_id, pharmacy_id, clear_if_different=bool(clear_existing))
    except ValueError as ve:
        if str(ve).startswith("CROSS_PHARMACY_CONFLICT:"):
            parts = str(ve).split(":")
            old_name = parts[1] if len(parts) > 1 else "another pharmacy"
            new_name = parts[2] if len(parts) > 2 else "new pharmacy"
            return jsonify({
                "error": f"Your cart contains items from '{old_name}'. Each order must be fulfilled by a single pharmacy.",
                "conflict": True,
                "current_pharmacy": old_name,
                "target_pharmacy": new_name
            }), 409
        return jsonify({"error": str(ve)}), 400

    target_pharmacy_id = cart["pharmacy_id"]

    # Verify stock availability
    stock_row = query_db("""
        SELECT stock_quantity, is_available FROM pharmacy_inventory
        WHERE pharmacy_id = ? AND medicine_id = ?
    """, (target_pharmacy_id, medicine_id), one=True)

    if not stock_row or not stock_row["is_available"]:
        return jsonify({"error": "This medicine is currently out of stock at this pharmacy."}), 400

    conn = get_db()
    cur = conn.cursor()

    # Check if item already in cart
    existing = query_db("SELECT id, quantity FROM cart_items WHERE cart_id = ? AND medicine_id = ?", (cart["id"], medicine_id), one=True)
    if existing:
        new_qty = existing["quantity"] + quantity
        if new_qty > stock_row["stock_quantity"]:
            return jsonify({"error": f"Cannot add {quantity} more. Stock limit of {stock_row['stock_quantity']} reached."}), 400
        cur.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_qty, existing["id"]))
    else:
        if quantity > stock_row["stock_quantity"]:
            return jsonify({"error": f"Requested quantity ({quantity}) exceeds available stock ({stock_row['stock_quantity']})."}), 400
        cur.execute("INSERT INTO cart_items (cart_id, medicine_id, quantity) VALUES (?, ?, ?)", (cart["id"], medicine_id, quantity))

    conn.commit()
    return jsonify({"status": "success", "message": "Medicine added to cart."})

@cart_bp.route("/items/<int:item_id>", methods=["PUT"])
@login_required
def update_cart_item(item_id: int):
    data = request.get_json() or {}
    quantity = data.get("quantity")
    
    if quantity is None or quantity < 0:
        return jsonify({"error": "Valid quantity >= 0 is required."}), 400

    user_id = session["user_id"]
    cart = query_db("SELECT id, pharmacy_id FROM carts WHERE user_id = ?", (user_id,), one=True)
    if not cart:
        return jsonify({"error": "Cart not found."}), 404

    conn = get_db()
    cur = conn.cursor()

    if quantity == 0:
        cur.execute("DELETE FROM cart_items WHERE cart_id = ? AND (id = ? OR medicine_id = ?)", (cart["id"], item_id, item_id))
    else:
        # Resolve cart_item row to check stock bounds
        existing = query_db("SELECT id, medicine_id FROM cart_items WHERE cart_id = ? AND (id = ? OR medicine_id = ?)", (cart["id"], item_id, item_id), one=True)
        if not existing:
            return jsonify({"error": "Item not found in cart."}), 404
        med_id = existing["medicine_id"]
        stock_row = query_db("SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = ? AND medicine_id = ?", (cart["pharmacy_id"], med_id), one=True)
        if stock_row and quantity > stock_row["stock_quantity"]:
            return jsonify({"error": f"Requested quantity exceeds available stock ({stock_row['stock_quantity']})."}), 400
        cur.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (quantity, existing["id"]))

    conn.commit()
    return jsonify({"status": "success", "message": "Cart updated."})

@cart_bp.route("/items/<int:item_id>", methods=["DELETE"])
@login_required
def remove_cart_item(item_id: int):
    user_id = session["user_id"]
    cart = query_db("SELECT id FROM carts WHERE user_id = ?", (user_id,), one=True)
    if cart:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM cart_items WHERE cart_id = ? AND (id = ? OR medicine_id = ?)", (cart["id"], item_id, item_id))
        conn.commit()
    return jsonify({"status": "success", "message": "Item removed from cart."})

@cart_bp.route("", methods=["DELETE"])
@login_required
def clear_cart():
    user_id = session["user_id"]
    cart = query_db("SELECT id FROM carts WHERE user_id = ?", (user_id,), one=True)
    if cart:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart["id"],))
        conn.commit()
    return jsonify({"status": "success", "message": "Cart cleared."})
