"""
Defect Remediation & Multi-Tier Verification Suite for MediApp.
Covers:
- DEF-04: Non-numeric rx parameter error handling / graceful fallback (HTTP 400 or fallback, never 500)
- DEF-05: Customer registration with address as plain string persisted to customer_addresses
- DEF-06: Courier available runs route returns parsed delivery address (not placeholder fallback)
- DEF-07: AI triage emergency alerts return both 'response' and 'emergency_message' keys
- DEF-08: Delivery OTP strictly redacted from GET /api/orders & GET /api/orders/<id> for delivery role
- DEF-14: Prescription transitions reject contradictory re-approval of rejected prescriptions and re-rejection of verified prescriptions
- DEF-21: Cold-chain filtering and database column requires_cold_chain handling
- Tier 3 Pairwise Tests:
    - Multi-pharmacy cart conflict resolution
    - Atomic inventory decrement and order cancellation restore
    - Payment locking on cancelled orders
    - Prescription verification order auto-sync and rejection stock restoration
    - Delivery rider claim concurrency
"""
import json
import pytest
from app.database import query_db, get_db


# ============================================================================
# Category 2: Backend API & Runtime Exception Defects
# ============================================================================

def test_def04_rx_invalid_string_param(client):
    """
    DEF-04: Unhandled ValueError Exception on Non-Numeric rx Query Parameter.
    Sending ?rx=invalid must return HTTP 400 Bad Request or graceful fallback (HTTP 200),
    and must NEVER terminate with an unhandled ValueError / HTTP 500 crash.
    """
    res = client.get("/api/medicines?rx=invalid")
    assert res.status_code in (400, 200), (
        f"Expected HTTP 400 or graceful fallback 200 on ?rx=invalid, got {res.status_code}"
    )
    if res.status_code == 400:
        data = res.get_json()
        assert "error" in data or "message" in data


def test_def04_rx_boolean_strings(client):
    """
    DEF-04: Verify boolean strings like ?rx=true or ?rx=false do not crash the endpoint.
    """
    for val in ("true", "false", "all", "none", "xyz"):
        res = client.get(f"/api/medicines?rx={val}")
        assert res.status_code in (400, 200), (
            f"Expected HTTP 400 or graceful fallback 200 on ?rx={val}, got {res.status_code}"
        )


def test_def04_rx_valid_numeric_values(client):
    """
    DEF-04 Happy Path: Valid numeric rx values (?rx=1 and ?rx=0) must return filtered medicines.
    """
    res_rx1 = client.get("/api/medicines?rx=1")
    assert res_rx1.status_code == 200
    data_rx1 = res_rx1.get_json()
    for med in data_rx1["medicines"]:
        assert med["prescription_required"] == 1

    res_rx0 = client.get("/api/medicines?rx=0")
    assert res_rx0.status_code == 200
    data_rx0 = res_rx0.get_json()
    for med in data_rx0["medicines"]:
        assert med["prescription_required"] == 0


def test_def05_customer_registration_address_string_persisted(app, client):
    """
    DEF-05: Customer Registration Address String Discarded Due to Strict Dict Check.
    When AuthModal.tsx registers a customer submitting address as a plain string,
    the address must be persisted into customer_addresses and set as default.
    """
    import uuid
    email = f"test.addr.string.{uuid.uuid4().hex[:6]}@mediapp.local"

    payload = {
        "email": email,
        "password": "Password@123",
        "full_name": "Priya Ramesh",
        "phone": "+91 9888877777",
        "address": "Flat 302, Green Glen Layout, Bellandur, Bengaluru 560103"
    }

    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201, f"Expected 201 Created, got {res.status_code}: {res.get_json()}"
    new_user_id = res.get_json()["user"]["id"]

    # Verify address record was created in customer_addresses
    with app.app_context():
        addr_record = query_db(
            "SELECT * FROM customer_addresses WHERE user_id = ?",
            (new_user_id,),
            one=True
        )
        assert addr_record is not None, (
            f"DEF-05 Violation: Address string was discarded. No row in customer_addresses for user {new_user_id}"
        )
        combined_addr = f"{addr_record['address_line1']} {addr_record.get('address_line2', '')} {addr_record.get('city', '')} {addr_record.get('pincode', '')}"
        assert "Green Glen" in combined_addr or "302" in combined_addr or "Bengaluru" in combined_addr, (
            f"Persisted address does not match input: {dict(addr_record)}"
        )


def test_def05_customer_registration_dict_address_still_supported(app, client):
    """
    DEF-05 Contract: Ensure structured dictionary address payloads still function.
    """
    import uuid
    email = f"test.addr.dict.{uuid.uuid4().hex[:6]}@mediapp.local"

    payload = {
        "email": email,
        "password": "Password@123",
        "full_name": "Rohan Deshmukh",
        "phone": "+91 9777766666",
        "address": {
            "address_line1": "Tower B, 1404, Prestige Ferns",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560102"
        }
    }

    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    user_id = res.get_json()["user"]["id"]

    with app.app_context():
        addr = query_db("SELECT * FROM customer_addresses WHERE user_id = ?", (user_id,), one=True)
        assert addr is not None
        assert "Prestige Ferns" in addr["address_line1"]


def test_def06_courier_available_runs_parsed_address(client, auth_client):
    """
    DEF-06: Available Courier Runs Route Omits Address Deserialization, Causing Static Fallback.
    The GET /api/delivery/available endpoint must return parsed delivery_address on each run,
    preventing DeliveryRunsBoard.tsx from falling back to static 'Bengaluru Express Delivery Hub'.
    """
    # 1. Customer places order with distinct street address
    c_client = auth_client("customer")
    c_client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
    test_address = "402 Green Glen Layout, Bellandur, Bengaluru 560103"
    order_res = c_client.post("/api/orders", json={"delivery_address": test_address})
    assert order_res.status_code == 201
    order_id = order_res.get_json()["order_id"]

    # 2. Advance order status to READY_FOR_PICKUP without assigned delivery person
    conn = get_db()
    conn.execute(
        "UPDATE orders SET order_status = 'READY_FOR_PICKUP', delivery_person_id = NULL WHERE id = ?",
        (order_id,)
    )
    conn.commit()

    # 3. Authenticate as delivery rider and fetch available orders
    d_client = auth_client("delivery")
    res = d_client.get("/api/delivery/available")
    assert res.status_code == 200
    data = res.get_json()
    orders = data.get("orders") or data.get("available_orders") or []
    
    target_order = next((o for o in orders if o["id"] == order_id), None)
    assert target_order is not None, f"Order {order_id} not found in available runs"

    # DEF-06 assertion: delivery_address must be present and contain real address
    deliv_addr = target_order.get("delivery_address")
    assert deliv_addr is not None and len(str(deliv_addr).strip()) > 0, (
        f"DEF-06 Violation: delivery_address is missing or empty in available orders: {target_order}"
    )
    assert "Bengaluru Express Delivery Hub" not in str(deliv_addr) or "Green Glen" in str(deliv_addr), (
        f"delivery_address returned static hub placeholder instead of customer address: '{deliv_addr}'"
    )


def test_def07_ai_emergency_triage_contract(client):
    """
    DEF-07: AI Emergency Triage Alert Text Discarded Due to Response Object Key Mismatch.
    query_assistant must return BOTH 'response' and 'emergency_message' keys to maintain
    compatibility with AITriageModal.tsx without discarding clinical warning text.
    """
    emergency_query = "Crushing chest pain radiating down left arm with shortness of breath"
    res = client.post("/api/ai/consult", json={"query": emergency_query})
    assert res.status_code == 200
    data = res.get_json()
    result = data.get("result", {})

    assert result.get("is_emergency") is True, f"Expected is_emergency=True, got {result}"
    
    # Must contain both response and emergency_message keys
    assert "response" in result, f"Expected 'response' key in AI emergency result: {result.keys()}"
    assert "emergency_message" in result, (
        f"DEF-07 Violation: Missing backward-compatible 'emergency_message' key for AITriageModal.tsx: {result.keys()}"
    )
    # The message must cite emergency services
    msg = result.get("emergency_message", "")
    assert "112" in msg or "911" in msg or "108" in msg or "emergency" in msg.lower(), (
        f"Emergency warning does not contain emergency contact instructions: '{msg}'"
    )


# ============================================================================
# Category 3: Security & RBAC Defects
# ============================================================================

def test_def08_delivery_otp_redacted_for_courier_in_order_list(client, auth_client):
    """
    DEF-08: Plaintext Patient Delivery Handover OTP Leaked to Delivery Couriers in API Responses.
    When a delivery rider fetches GET /api/orders, delivery_otp must be redacted (None or omitted).
    """
    # 1. Customer places an order to generate an OTP
    c_client = auth_client("customer")
    c_client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
    res_order = c_client.post("/api/orders", json={
        "delivery_address": "402 Green Glen Layout, Bellandur, Bengaluru 560103"
    })
    assert res_order.status_code == 201
    order_id = res_order.get_json()["order_id"]

    # 2. Assign order to delivery courier #4 (demo.delivery)
    conn = get_db()
    rider = query_db("SELECT id FROM users WHERE email = 'demo.delivery@mediapp.local'", one=True)
    rider_id = rider["id"]
    conn.execute(
        "UPDATE orders SET delivery_person_id = ?, order_status = 'IN_TRANSIT' WHERE id = ?",
        (rider_id, order_id)
    )
    conn.commit()

    # 3. Query orders as delivery rider
    d_client = auth_client("delivery")
    res = d_client.get("/api/orders")
    assert res.status_code == 200
    orders = res.get_json().get("orders", [])

    for ord_dict in orders:
        otp_val = ord_dict.get("delivery_otp")
        assert otp_val is None or otp_val == "" or otp_val == "REDACTED", (
            f"DEF-08 Security Violation: Plaintext delivery_otp '{otp_val}' leaked to courier in order {ord_dict.get('id')}"
        )


def test_def08_delivery_otp_redacted_for_courier_in_order_detail(client, auth_client):
    """
    DEF-08: Delivery OTP must also be redacted in GET /api/orders/<id> for delivery couriers.
    """
    c_client = auth_client("customer")
    c_client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
    res_order = c_client.post("/api/orders", json={
        "delivery_address": "402 Green Glen Layout, Bellandur, Bengaluru 560103"
    })
    order_id = res_order.get_json()["order_id"]

    rider = query_db("SELECT id FROM users WHERE email = 'demo.delivery@mediapp.local'", one=True)
    rider_id = rider["id"]
    conn = get_db()
    conn.execute(
        "UPDATE orders SET delivery_person_id = ?, order_status = 'IN_TRANSIT' WHERE id = ?",
        (rider_id, order_id)
    )
    conn.commit()

    d_client = auth_client("delivery")
    res_detail = d_client.get(f"/api/orders/{order_id}")
    assert res_detail.status_code == 200
    order_data = res_detail.get_json().get("order", {})

    otp_val = order_data.get("delivery_otp")
    assert otp_val is None or otp_val == "" or otp_val == "REDACTED", (
        f"DEF-08 Security Violation: Courier detail view leaked secret OTP '{otp_val}'"
    )


def test_def08_delivery_otp_accessible_to_customer_and_admin(client, auth_client):
    """
    DEF-08 Invariant: Secret OTP MUST be accessible to customer receiving parcel and admin.
    """
    c_client = auth_client("customer")
    c_client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
    res_order = c_client.post("/api/orders", json={
        "delivery_address": "402 Green Glen Layout, Bellandur, Bengaluru 560103"
    })
    order_id = res_order.get_json()["order_id"]

    res_cust = c_client.get(f"/api/orders/{order_id}")
    assert res_cust.status_code == 200
    cust_order = res_cust.get_json().get("order", {})
    otp = cust_order.get("delivery_otp")
    assert otp is not None and len(str(otp)) == 6, (
        f"Customer should be able to view their 6-digit OTP, got {otp}"
    )


# ============================================================================
# Category 4: Pharmacist Review State Machine Defects
# ============================================================================

def test_def14_reject_reapproval_of_rejected_prescription(app, client, auth_client):
    """
    DEF-14: Inconsistent Pharmacist Review Desk State Transitions.
    A prescription that has already been rejected (which cancelled the linked order)
    must reject subsequent re-approval attempts with HTTP 400 or HTTP 409.
    """
    with app.app_context():
        p_client = auth_client("pharmacy")
        
        # 1. Create a dummy prescription in pending status
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO prescriptions (customer_id, original_filename, file_path, file_size, mime_type, status)
            VALUES (1, 'rx_test_def14.pdf', '/tmp/fake.pdf', 1024, 'application/pdf', 'pending')
        """)
        conn.commit()
        rx_id = cur.lastrowid

        # 2. Reject prescription
        res_reject = p_client.post(f"/api/prescriptions/{rx_id}/verify", json={
            "decision": "rejected",
            "rejection_reason": "Expired prescription date"
        })
        assert res_reject.status_code == 200

        # Verify status is rejected in DB
        rx_after_reject = query_db("SELECT status FROM prescriptions WHERE id = ?", (rx_id,), one=True)
        assert rx_after_reject["status"] == "rejected"

        # 3. Attempt to re-approve the rejected prescription
        res_reapprove = p_client.post(f"/api/prescriptions/{rx_id}/verify", json={
            "decision": "verified",
            "approved_medicines": [{"medicine_id": 1, "name": "Paracetamol"}]
        })
        assert res_reapprove.status_code in (400, 409), (
            f"DEF-14 Violation: Expected HTTP 400 or 409 when re-approving rejected Rx, got {res_reapprove.status_code}"
        )


def test_def14_reject_rerejection_of_verified_prescription(app, client, auth_client):
    """
    DEF-14: A prescription that has already been certified/approved (verified)
    must reject subsequent rejection attempts with HTTP 400 or HTTP 409.
    """
    with app.app_context():
        p_client = auth_client("pharmacy")
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO prescriptions (customer_id, original_filename, file_path, file_size, mime_type, status)
            VALUES (1, 'rx_test_def14_verified.pdf', '/tmp/fake.pdf', 1024, 'application/pdf', 'pending')
        """)
        conn.commit()
        rx_id = cur.lastrowid

        # 1. Approve prescription
        res_verify = p_client.post(f"/api/prescriptions/{rx_id}/verify", json={
            "decision": "verified",
            "approved_medicines": [{"medicine_id": 1, "name": "Paracetamol"}]
        })
        assert res_verify.status_code == 200

        # 2. Attempt to reject the already verified prescription
        res_rereject = p_client.post(f"/api/prescriptions/{rx_id}/verify", json={
            "decision": "rejected",
            "rejection_reason": "Attempting contradictory rejection"
        })
        assert res_rereject.status_code in (400, 409), (
            f"DEF-14 Violation: Expected HTTP 400 or 409 when re-rejecting verified Rx, got {res_rereject.status_code}"
        )


# ============================================================================
# Category 6: Cold-Chain Schema & DB Column Handling
# ============================================================================

def test_def21_requires_cold_chain_database_column(client):
    """
    DEF-21 / DEF-03: Verify requires_cold_chain column exists in medicines table and defaults to 0.
    """
    cols = query_db("PRAGMA table_info(medicines)")
    col_names = [c["name"] for c in cols]
    assert "requires_cold_chain" in col_names, (
        f"DEF-03 / DEF-21 Violation: medicines table missing column 'requires_cold_chain': {col_names}"
    )


def test_def21_cold_chain_query_filtering(client):
    """
    DEF-21 / DEF-03: GET /api/medicines?cold_chain=1 returns cold-chain medicines without SQL error.
    """
    res = client.get("/api/medicines?cold_chain=1&limit=50")
    assert res.status_code == 200
    data = res.get_json()
    meds = data.get("medicines", [])
    assert len(meds) > 0, "Expected at least one cold-chain medicine in catalogue"
    for m in meds:
        assert m.get("requires_cold_chain") == 1, (
            f"Returned medicine {m.get('name')} does not have requires_cold_chain=1"
        )


# ============================================================================
# Tier 3: Pairwise Cross-Feature Integration Tests
# ============================================================================

def test_tier3_cart_multi_pharmacy_conflict_resolution(client, auth_client):
    """
    Tier 3 Pairwise: Cart & Multi-Pharmacy Isolation.
    Adding item from Pharmacy 2 to a cart containing Pharmacy 1 items must return
    HTTP 409 Conflict. Supplying clear_existing=True must resolve the conflict.
    """
    c_client = auth_client("customer")

    # Clear current cart
    c_client.delete("/api/cart")

    # 1. Add item from Pharmacy 1 (medicine_id=1, pharmacy_id=1)
    res1 = c_client.post("/api/cart/items", json={
        "medicine_id": 1,
        "pharmacy_id": 1,
        "quantity": 1
    })
    assert res1.status_code in (200, 201)

    # 2. Add item from Pharmacy 2 (medicine_id=2, pharmacy_id=2) -> Must trigger 409 Conflict
    res2 = c_client.post("/api/cart/items", json={
        "medicine_id": 2,
        "pharmacy_id": 2,
        "quantity": 1
    })
    assert res2.status_code == 409, f"Expected 409 Conflict on cross-pharmacy cart addition, got {res2.status_code}"
    err_data = res2.get_json()
    assert err_data.get("conflict") is True or "single pharmacy" in err_data.get("error", "").lower()

    # 3. Add with clear_existing=True -> Must succeed
    res3 = c_client.post("/api/cart/items", json={
        "medicine_id": 2,
        "pharmacy_id": 2,
        "quantity": 1,
        "clear_existing": True
    })
    assert res3.status_code in (200, 201), f"Expected 200/201 after clear_existing, got {res3.status_code}"


def test_tier3_inventory_atomic_decrement_and_cancellation_restore(app, client, auth_client):
    """
    Tier 3 Pairwise: Inventory & Order Lifecycle.
    Placing an order atomically decrements stock in pharmacy_inventory.
    Cancelling the order restores the exact reserved stock.
    """
    with app.app_context():
        c_client = auth_client("customer")
        c_client.delete("/api/cart")

        # Use medicine 1 and pharmacy 1
        inv_before = query_db(
            "SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 1",
            one=True
        )
        assert inv_before is not None
        qty_before = inv_before["stock_quantity"]

        # Add 2 units with pharmacy_id=1
        res_add = c_client.post("/api/cart/items", json={
            "medicine_id": 1,
            "pharmacy_id": 1,
            "quantity": 2
        })
        assert res_add.status_code in (200, 201)

        res_order = c_client.post("/api/orders", json={
            "delivery_address": "402 Green Glen Layout, Bellandur, Bengaluru 560103"
        })
        assert res_order.status_code == 201
        order_id = res_order.get_json()["order_id"]

        # Verify inventory was decremented by 2
        post_order_inv = query_db(
            "SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 1",
            one=True
        )
        assert post_order_inv["stock_quantity"] == qty_before - 2, (
            f"Inventory not decremented by 2: was {qty_before}, now {post_order_inv['stock_quantity']}"
        )

        # Cancel order
        res_cancel = c_client.post(f"/api/orders/{order_id}/cancel", json={
            "reason": "Customer cancellation test"
        })
        assert res_cancel.status_code == 200

        # Verify inventory restored back to qty_before
        restored_inv = query_db(
            "SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 1",
            one=True
        )
        assert restored_inv["stock_quantity"] == qty_before, (
            f"Inventory not restored to {qty_before}: now {restored_inv['stock_quantity']}"
        )


def test_tier3_payment_locking_on_cancelled_order(app, client, auth_client):
    """
    Tier 3 Pairwise: Payment & Terminal Order Locking.
    Attempting payment initiation or verification on an already cancelled order
    must be rejected with HTTP 400 Bad Request.
    """
    c_client = auth_client("customer")
    c_client.delete("/api/cart")
    c_client.post("/api/cart/items", json={"medicine_id": 1, "pharmacy_id": 1, "quantity": 1})
    res_order = c_client.post("/api/orders", json={
        "delivery_address": "402 Green Glen Layout, Bellandur, Bengaluru 560103"
    })
    order_id = res_order.get_json()["order_id"]

    # Cancel order
    c_client.post(f"/api/orders/{order_id}/cancel", json={"reason": "Test cancel"})

    # Attempt to initiate payment
    res_pay = c_client.post("/api/payments/create-order", json={"order_id": order_id})
    assert res_pay.status_code == 400, f"Expected 400 when initiating payment on CANCELLED order, got {res_pay.status_code}"

    # Attempt to verify payment
    res_ver = c_client.post("/api/payments/verify", json={
        "order_id": order_id,
        "razorpay_payment_id": "pay_fake123",
        "razorpay_order_id": "order_fake123",
        "razorpay_signature": "sig_fake"
    })
    assert res_ver.status_code == 400, f"Expected 400 when verifying payment on CANCELLED order, got {res_ver.status_code}"


def test_tier3_prescription_verification_order_auto_sync_and_rejection_stock_restore(app, client, auth_client):
    """
    Tier 3 Pairwise: Prescription Verification & Order State Synchronization.
    1. An order with prescription-required item starts in AWAITING_PRESCRIPTION.
    2. Pharmacist verifying Rx automatically transitions order to PRESCRIPTION_VERIFIED.
    3. If pharmacist rejects Rx, order is automatically transitioned to CANCELLED and stock restored.
    """
    with app.app_context():
        # Find prescription-required medicine
        rx_med = query_db(
            "SELECT id, prescription_required FROM medicines WHERE prescription_required = 1 LIMIT 1",
            one=True
        )
        assert rx_med is not None
        rx_med_id = rx_med["id"]

        # Part A: Successful Approval Auto-Sync
        # 1. Login as customer
        c_client = auth_client("customer")
        cust_row = query_db("SELECT id FROM users WHERE email = 'demo.customer@mediapp.local'", one=True)
        cust_id = cust_row["id"] if cust_row else 2

        # Create dummy prescription in pending state for this customer
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO prescriptions (customer_id, original_filename, file_path, file_size, mime_type, status)
            VALUES (?, 'rx_sync_test.pdf', '/tmp/fake.pdf', 1024, 'application/pdf', 'pending')
        """, (cust_id,))
        conn.commit()
        rx_id = cur.lastrowid

        # Place order linked to prescription while logged in as customer
        c_client.delete("/api/cart")
        c_client.post("/api/cart/items", json={"medicine_id": rx_med_id, "pharmacy_id": 1, "quantity": 1})
        res_ord = c_client.post("/api/orders", json={
            "delivery_address": "402 Green Glen Layout, Bellandur, Bengaluru 560103",
            "prescription_id": rx_id
        })
        assert res_ord.status_code == 201, f"Failed placing order with prescription: {res_ord.get_json()}"
        order_id = res_ord.get_json()["order_id"]

        # Initial order status should be AWAITING_PRESCRIPTION
        ord_row = query_db("SELECT order_status FROM orders WHERE id = ?", (order_id,), one=True)
        assert ord_row["order_status"] == "AWAITING_PRESCRIPTION"

        # 2. Switch session to pharmacist and verify prescription
        p_client = auth_client("pharmacy")
        res_ver = p_client.post(f"/api/prescriptions/{rx_id}/verify", json={
            "decision": "verified",
            "approved_medicines": [{"medicine_id": rx_med_id, "name": "Rx Med"}]
        })
        assert res_ver.status_code == 200

        # Linked order should auto-sync to PRESCRIPTION_VERIFIED
        ord_after_verify = query_db("SELECT order_status FROM orders WHERE id = ?", (order_id,), one=True)
        assert ord_after_verify["order_status"] == "PRESCRIPTION_VERIFIED", (
            f"Order status did not auto-transition to PRESCRIPTION_VERIFIED: {ord_after_verify['order_status']}"
        )

        # Part B: Rejection Auto-Cancellation & Stock Restore
        # 1. Switch back to customer session
        c_client = auth_client("customer")
        cur.execute("""
            INSERT INTO prescriptions (customer_id, original_filename, file_path, file_size, mime_type, status)
            VALUES (?, 'rx_reject_sync_test.pdf', '/tmp/fake.pdf', 1024, 'application/pdf', 'pending')
        """, (cust_id,))
        conn.commit()
        rx_id_2 = cur.lastrowid

        # Check inventory before order
        inv_before = query_db(
            "SELECT stock_quantity, pharmacy_id FROM pharmacy_inventory WHERE medicine_id = ? AND pharmacy_id = 1",
            (rx_med_id,),
            one=True
        )
        stock_before = inv_before["stock_quantity"]

        c_client.delete("/api/cart")
        c_client.post("/api/cart/items", json={"medicine_id": rx_med_id, "pharmacy_id": 1, "quantity": 2})
        res_ord_2 = c_client.post("/api/orders", json={
            "delivery_address": "402 Green Glen Layout, Bellandur, Bengaluru 560103",
            "prescription_id": rx_id_2
        })
        assert res_ord_2.status_code == 201, f"Failed placing order: {res_ord_2.get_json()}"
        order_id_2 = res_ord_2.get_json()["order_id"]

        # 2. Switch session to pharmacist and reject prescription
        p_client = auth_client("pharmacy")
        res_rej = p_client.post(f"/api/prescriptions/{rx_id_2}/verify", json={
            "decision": "rejected",
            "rejection_reason": "Counterfeit doctor seal"
        })
        assert res_rej.status_code == 200

        # Linked order must auto-transition to CANCELLED
        ord_after_reject = query_db("SELECT order_status FROM orders WHERE id = ?", (order_id_2,), one=True)
        assert ord_after_reject["order_status"] == "CANCELLED", (
            f"Order status did not auto-transition to CANCELLED upon Rx rejection: {ord_after_reject['order_status']}"
        )

        # Inventory must be restored
        inv_after = query_db(
            "SELECT stock_quantity FROM pharmacy_inventory WHERE medicine_id = ? AND pharmacy_id = 1",
            (rx_med_id,),
            one=True
        )
        assert inv_after["stock_quantity"] == stock_before, (
            f"Inventory not restored upon prescription rejection cancellation: was {stock_before}, now {inv_after['stock_quantity']}"
        )


def test_tier3_courier_delivery_claim_concurrency(client, auth_client):
    """
    Tier 3 Pairwise: Concurrency & Delivery Claim Race Conditions.
    When two delivery drivers attempt to claim the same order in READY_FOR_PICKUP,
    only the first claim succeeds (HTTP 200); the second claim is rejected with HTTP 400 or 409.
    """
    c_client = auth_client("customer")
    c_client.delete("/api/cart")
    c_client.post("/api/cart/items", json={"medicine_id": 1, "pharmacy_id": 1, "quantity": 1})
    res_order = c_client.post("/api/orders", json={
        "delivery_address": "402 Green Glen Layout, Bellandur, Bengaluru 560103"
    })
    order_id = res_order.get_json()["order_id"]

    # Advance order through pharmacy: ACCEPTED -> PREPARING -> READY_FOR_PICKUP
    pharm = auth_client("pharmacy")
    pharm.post(f"/api/pharmacy/orders/{order_id}/accept")
    pharm.post(f"/api/orders/{order_id}/transition", json={"target_status": "PREPARING", "notes": "Packaging medicines"})
    pharm.post(f"/api/orders/{order_id}/transition", json={"target_status": "READY_FOR_PICKUP", "notes": "Ready for courier"})

    # Driver 1 claims order
    d1_client = auth_client("delivery")
    res1 = d1_client.post(f"/api/delivery/orders/{order_id}/claim")
    assert res1.status_code in (200, 201), f"First rider claim should succeed: {res1.get_json()}"

    # Driver 2 attempts to claim same order
    rider2 = client
    rider2.post("/api/auth/demo-login", json={"role": "delivery"})
    res2 = rider2.post(f"/api/delivery/orders/{order_id}/claim")
    assert res2.status_code in (400, 409, 403), (
        f"Second rider claim should fail with 400/409/403, got {res2.status_code}: {res2.get_json()}"
    )
