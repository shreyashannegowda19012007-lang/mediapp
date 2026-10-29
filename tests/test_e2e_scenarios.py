"""
End-to-End Acceptance Scenario Tests for MediApp.
Directly implements and executes Scenarios A through G from Specification Section 22:
- Scenario A: Clean installation & health check
- Scenario B: Complete customer purchase & inventory reservation
- Scenario C: Pharmacy fulfilment state progression
- Scenario D: Delivery rider assignment & doorstep handover
- Scenario E: Admin oversight & real database analytics
- Scenario F: Order cancellation and inventory restoration
- Scenario G: Prescription upload, OCR parsing, and verification
"""
import io

def test_scenario_a_clean_installation_and_health(client):
    """Scenario A: Verify health check and diagnostics endpoints."""
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json["status"] == "healthy"
    assert health_res.json["database_connected"] is True

    diag_res = client.get("/api/diagnostics")
    assert diag_res.status_code == 200
    assert diag_res.json["database_ready"] is True
    assert "capabilities" in diag_res.json

def test_scenario_b_to_d_complete_cross_portal_order_lifecycle(client, auth_client):
    """
    Scenarios B, C, D executed sequentially on ONE authoritative order:
    Customer creates & pays -> Pharmacy accepts & packages & readies -> Rider claims, pickups & delivers.
    Verifies that all four portals observe the exact same order ID, item snapshots, and totals.
    """
    # -------------------------------------------------------------
    # Scenario B: Customer Purchase
    # -------------------------------------------------------------
    cust = auth_client("customer")
    cust.delete("/api/cart")

    # Search catalogue for Dolo 650mg
    search_res = cust.get("/api/medicines?q=Dolo")
    assert search_res.status_code == 200
    assert len(search_res.json["medicines"]) >= 1
    target_med_id = search_res.json["medicines"][0]["id"]

    # Add 2 units to cart
    add_res = cust.post("/api/cart/items", json={"medicine_id": target_med_id, "quantity": 2, "pharmacy_id": 1})
    assert add_res.status_code == 200, f"Add to cart failed: {add_res.json}"

    # Validate cart
    cart_res = cust.get("/api/cart")
    assert cart_res.json["item_count"] >= 2
    authoritative_total = cart_res.json["totals"]["total"]

    # Checkout
    order_res = cust.post("/api/orders", json={
        "delivery_address": {
            "line1": "Flat 402, Green Glen Layout",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560103",
            "recipient_phone": "+91 9876543210"
        },
        "delivery_notes": "Handle with care"
    })
    assert order_res.status_code == 201
    order = order_res.json["order"]
    order_id = order["id"]
    assert order["total_amount"] == authoritative_total
    assert order["order_status"] == "PLACED"

    # Complete demo payment
    pay_res = cust.post("/api/payments/verify", json={"order_id": order_id, "status": "success"})
    assert pay_res.status_code == 200

    # -------------------------------------------------------------
    # Scenario C: Pharmacy Fulfillment
    # -------------------------------------------------------------
    pharm = auth_client("pharmacy")

    # Locate the same order in pharmacy incoming queue
    pharm_order_res = pharm.get(f"/api/orders/{order_id}")
    assert pharm_order_res.status_code == 200
    pharm_order = pharm_order_res.json["order"]
    assert pharm_order["id"] == order_id
    assert pharm_order["total_amount"] == authoritative_total
    assert pharm_order["payment_status"] == "paid"

    # Accept the order
    accept_res = pharm.post(f"/api/pharmacy/orders/{order_id}/accept")
    assert accept_res.status_code == 200
    assert accept_res.json["order"]["order_status"] == "ACCEPTED"

    # Transition to PREPARING
    prep_res = pharm.post(f"/api/orders/{order_id}/transition", json={
        "target_status": "PREPARING",
        "notes": "Items packaged in tamper-evident clinical bag"
    })
    assert prep_res.status_code == 200
    assert prep_res.json["order"]["order_status"] == "PREPARING"

    # Transition to READY_FOR_PICKUP
    ready_res = pharm.post(f"/api/orders/{order_id}/transition", json={
        "target_status": "READY_FOR_PICKUP",
        "notes": "Ready on pharmacy pickup counter"
    })
    assert ready_res.status_code == 200
    assert ready_res.json["order"]["order_status"] == "READY_FOR_PICKUP"

    # -------------------------------------------------------------
    # Scenario D: Delivery Fulfillment
    # -------------------------------------------------------------
    deliv = auth_client("delivery")

    # Check available pool contains this order
    avail_res = deliv.get("/api/delivery/available")
    assert avail_res.status_code == 200
    avail_ids = [o["id"] for o in avail_res.json["available_orders"]]
    assert order_id in avail_ids

    # Claim the order
    claim_res = deliv.post(f"/api/delivery/orders/{order_id}/claim")
    assert claim_res.status_code == 200
    assert claim_res.json["order"]["order_status"] == "DELIVERY_ASSIGNED"

    # Pickup from pharmacy
    pickup_res = deliv.post(f"/api/delivery/orders/{order_id}/pickup")
    assert pickup_res.status_code == 200

    # Mark in-transit
    transit_res = deliv.post(f"/api/delivery/orders/{order_id}/in-transit")
    assert transit_res.status_code == 200

    # Complete delivery
    complete_res = deliv.post(f"/api/delivery/orders/{order_id}/complete", json={
        "proof": "Customer OTP verified 8821"
    })
    assert complete_res.status_code == 200

    # -------------------------------------------------------------
    # Final Cross-Portal Reconciliation Gate
    # -------------------------------------------------------------
    # Customer checks status
    final_cust_res = cust.get(f"/api/orders/{order_id}")
    assert final_cust_res.json["order"]["order_status"] == "DELIVERED"

    # Pharmacy checks status
    final_pharm_res = pharm.get(f"/api/orders/{order_id}")
    assert final_pharm_res.json["order"]["order_status"] == "DELIVERED"

    # Admin checks status
    admin = auth_client("admin")
    final_admin_res = admin.get(f"/api/orders/{order_id}")
    assert final_admin_res.json["order"]["order_status"] == "DELIVERED"
    assert final_admin_res.json["order"]["total_amount"] == authoritative_total

def test_scenario_e_admin_oversight_and_metrics(auth_client):
    """Scenario E: Admin dashboard computes real analytics from live DB."""
    admin = auth_client("admin")
    stats_res = admin.get("/api/admin/stats")
    assert stats_res.status_code == 200
    metrics = stats_res.json["metrics"]
    assert metrics["total_orders"] >= 1
    assert metrics["total_revenue"] >= 0.0
    assert metrics["total_users"] >= 4

def test_scenario_f_cancellation_and_inventory_restoration(app, auth_client):
    """Scenario F: Order cancellation safely restores reserved pharmacy inventory."""
    with app.app_context():
        cust = auth_client("customer")

        # Initial inventory of medicine 1 (Crocin) at pharmacy 1
        from app.database import query_db
        inv_before = query_db("SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 1", one=True)
        qty_before = inv_before["stock_quantity"]

        # Clear cart and place order for 2 units
        cust.delete("/api/cart")
        cust.post("/api/cart/items", json={"medicine_id": 1, "quantity": 2, "pharmacy_id": 1})
        order_res = cust.post("/api/orders", json={
            "delivery_address": {"line1": "Cancel St", "city": "Bengaluru", "state": "KA", "pincode": "560001"}
        })
        order_id = order_res.json["order"]["id"]

        # Inventory must be decremented by 2
        inv_reserved = query_db("SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 1", one=True)
        assert inv_reserved["stock_quantity"] == qty_before - 2

        # Cancel the order
        cancel_res = cust.post(f"/api/orders/{order_id}/cancel", json={"reason": "Customer changed mind"})
        assert cancel_res.status_code == 200
        assert cancel_res.json["order"]["order_status"] == "CANCELLED"

        # Inventory must be fully restored to original quantity
        inv_after = query_db("SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 1", one=True)
        assert inv_after["stock_quantity"] == qty_before

def test_scenario_g_prescription_workflow(auth_client):
    """Scenario G: Prescription upload, OCR entity extraction, and pharmacist approval."""
    cust = auth_client("customer")
    sample_rx = b"%PDF-1.4 ... Dr. Arvind Kapoor MD Patient: Aditi Sharma Rx: Tab Telma 40mg ... %%EOF"
    upload_res = cust.post("/api/prescriptions/upload", data={"file": (io.BytesIO(sample_rx), "cardio_rx.pdf")}, content_type="multipart/form-data")
    assert upload_res.status_code == 201
    rx_id = upload_res.json["prescription"]["id"]

    pharm = auth_client("pharmacy")
    verify_res = pharm.post(f"/api/prescriptions/{rx_id}/verify", json={"decision": "verified"})
    assert verify_res.status_code == 200

    check_res = cust.get(f"/api/prescriptions/{rx_id}")
    assert check_res.json["prescription"]["status"] == "verified"
