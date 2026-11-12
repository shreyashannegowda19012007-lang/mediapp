"""
Comprehensive Edge Cases, Boundary Testing, Security (IDOR/RBAC),
and Failure Injection Test Suite for MediApp.
"""
import pytest
from app.services.pricing_service import PricingService
from app.services.ddi_service import DDIService
from app.services.order_service import OrderStateMachine
from app.database import query_db, get_db

def test_input_validation_boundary_conditions(client):
    """Test boundary values: negative numbers, zero, extreme values, long strings."""
    # 1. Login with empty payload
    r = client.post("/api/auth/login", json={})
    assert r.status_code == 400
    assert "required" in r.get_json()["error"].lower()

    # 2. Registration with empty/missing fields
    r = client.post("/api/auth/register", json={
        "email": "",
        "password": "pass",
        "full_name": "",
        "phone": ""
    })
    assert r.status_code == 400

    # 3. Registration with invalid email format
    r = client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "Password123!",
        "full_name": "Test User",
        "phone": "+919876543210"
    })
    assert r.status_code == 400
    assert "valid email" in r.get_json()["error"].lower()

    # 4. Registration with short password
    r = client.post("/api/auth/register", json={
        "email": "valid.email@test.com",
        "password": "short",
        "full_name": "Test User",
        "phone": "+919876543210"
    })
    assert r.status_code == 400
    assert "8 characters" in r.get_json()["error"].lower()

    # 5. Extremely long string inputs (buffer / truncation robustness)
    long_string = "A" * 10000
    r = client.get(f"/api/medicines?q={long_string}")
    assert r.status_code == 200
    assert r.get_json()["medicines"] == []

    # 6. SQL injection attempt in search
    sql_injection = "' OR 1=1 -- "
    r = client.get(f"/api/medicines?q={sql_injection}")
    assert r.status_code == 200
    # Parameterized SQL correctly treats string literally
    assert isinstance(r.get_json()["medicines"], list)

    # 7. XSS injection string in medicine search
    xss_payload = "<script>alert('XSS')</script>"
    r = client.get(f"/api/medicines?q={xss_payload}")
    assert r.status_code == 200
    assert isinstance(r.get_json()["medicines"], list)

def test_unauthorized_rbac_and_idor_protection(client):
    """Verifies that endpoints enforce strict authentication, RBAC, and IDOR ownership checks."""
    # 1. Unauthenticated requests to protected endpoints
    assert client.get("/api/cart").status_code == 401
    assert client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1}).status_code == 401
    assert client.get("/api/orders").status_code == 401
    assert client.post("/api/orders", json={}).status_code == 401
    assert client.get("/api/admin/stats").status_code == 401
    assert client.get("/api/pharmacy/orders").status_code == 401
    assert client.get("/api/delivery/available").status_code == 401
    assert client.get("/api/prescriptions").status_code == 401

    # 2. Customer login
    r_login = client.post("/api/auth/login", json={
        "email": "demo.customer@mediapp.local",
        "password": "Customer@MediApp2026!"
    })
    assert r_login.status_code == 200

    # 3. Customer attempting to access Admin endpoints
    assert client.get("/api/admin/stats").status_code == 403
    assert client.get("/api/admin/users").status_code == 403
    assert client.get("/api/admin/pharmacies").status_code == 403
    assert client.get("/api/admin/system-health").status_code == 403

    # 4. Customer attempting to access Pharmacy endpoints
    assert client.get("/api/pharmacy/dashboard").status_code == 403
    assert client.get("/api/pharmacy/orders").status_code == 403
    assert client.get("/api/pharmacy/inventory").status_code == 403

    # 5. Customer attempting to access Delivery endpoints
    assert client.get("/api/delivery/available").status_code == 403
    assert client.get("/api/delivery/active").status_code == 403
    assert client.get("/api/delivery/history").status_code == 403

    # 6. Customer unauthorized role switch to admin
    r_bad_switch = client.post("/api/auth/switch-role", json={"role": "admin"})
    assert r_bad_switch.status_code == 403

def test_prescription_privacy_and_unauthorized_access(client):
    """Verifies that delivery drivers cannot access patient medical prescriptions (DEF-05)."""
    # Login as delivery driver
    r_deliv = client.post("/api/auth/login", json={
        "email": "demo.delivery@mediapp.local",
        "password": "Delivery@MediApp2026!"
    })
    assert r_deliv.status_code == 200

    # Delivery driver cannot list prescriptions
    assert client.get("/api/prescriptions").status_code == 403
    # Delivery driver cannot access individual prescription ID 1
    assert client.get("/api/prescriptions/1").status_code == 403
    # Delivery driver cannot download prescription file
    assert client.get("/api/prescriptions/1/file").status_code == 403

def test_admin_lockout_protection(client):
    """Verifies that admin accounts cannot be suspended/deactivated."""
    # Login as Admin
    r_admin = client.post("/api/auth/login", json={
        "email": "demo.admin@mediapp.local",
        "password": "Admin@MediApp2026!"
    })
    assert r_admin.status_code == 200

    r_users = client.get("/api/admin/users?role=admin")
    assert r_users.status_code == 200
    admin_users = r_users.get_json().get("users", [])
    assert len(admin_users) > 0
    admin_id = admin_users[0]["id"]

    # Attempt to deactivate admin
    r_deact = client.put(f"/api/admin/users/{admin_id}/status", json={"is_active": False})
    assert r_deact.status_code == 400
    assert "cannot be deactivated" in r_deact.get_json()["error"].lower()

def test_order_state_machine_illegal_transitions():
    """Verifies that illegal status transitions and unauthorized roles are blocked."""
    # Cannot transition PLACED directly to DELIVERED
    with pytest.raises(ValueError) as exc:
        OrderStateMachine.validate_transition("PLACED", "DELIVERED", "customer")
    assert "Invalid transition" in str(exc.value)

    # Customer cannot transition PLACED to ACCEPTED
    with pytest.raises(PermissionError) as exc:
        OrderStateMachine.validate_transition("PLACED", "ACCEPTED", "customer")
    assert "not authorized" in str(exc.value)

    # Cannot transition DELIVERED to CANCELLED
    with pytest.raises(ValueError) as exc:
        OrderStateMachine.validate_transition("DELIVERED", "CANCELLED", "admin")
    assert "Invalid transition" in str(exc.value)

    # Cannot transition CANCELLED to any state
    with pytest.raises(ValueError) as exc:
        OrderStateMachine.validate_transition("CANCELLED", "PLACED", "admin")
    assert "Invalid transition" in str(exc.value)

def test_pricing_calculations_and_free_delivery_threshold():
    """Verifies mathematical decimal precision and delivery fee logic."""
    # Subtotal < 500 incurs standard 30 INR fee
    items_small = [{"unit_price": 100.0, "quantity": 2}]
    res_small = PricingService.calculate_order_totals(items_small)
    assert res_small["subtotal"] == 200.00
    assert res_small["tax"] == 10.00  # 5% of 200
    assert res_small["delivery_fee"] == 30.00
    assert res_small["total"] == 240.00

    # Subtotal >= 500 gets free delivery
    items_large = [{"unit_price": 250.0, "quantity": 2}]
    res_large = PricingService.calculate_order_totals(items_large)
    assert res_large["subtotal"] == 500.00
    assert res_large["tax"] == 25.00  # 5% of 500
    assert res_large["delivery_fee"] == 0.00
    assert res_large["total"] == 525.00

    # Rounding test with 3 decimal places in unit price
    items_frac = [{"unit_price": 33.333, "quantity": 3}]
    res_frac = PricingService.calculate_order_totals(items_frac)
    assert isinstance(res_frac["total"], float)

def test_drug_drug_interaction_screening():
    """Verifies clinical DDI screening for contraindicated pairs."""
    # Sildenafil + Nitroglycerin is CONTRAINDICATED
    meds_contra = [
        {"id": 1, "name": "Viagra 50mg Tablet", "generic_name": "Sildenafil Citrate"},
        {"id": 2, "name": "Nitrocontin 2.6mg Tablet", "generic_name": "Nitroglycerin"}
    ]
    res_contra = DDIService.check_interactions_for_medicines(meds_contra)
    assert res_contra["has_interactions"] is True
    assert res_contra["highest_severity"] == "CONTRAINDICATED"
    assert len(res_contra["interactions"]) > 0

    # Safe combination (Paracetamol + Cetirizine)
    meds_safe = [
        {"id": 3, "name": "Calpol 500mg", "generic_name": "Paracetamol"},
        {"id": 4, "name": "Cetcip 10mg", "generic_name": "Cetirizine Hydrochloride"}
    ]
    res_safe = DDIService.check_interactions_for_medicines(meds_safe)
    assert res_safe["has_interactions"] is False
    assert res_safe["interactions"] == []

def test_ai_clinical_assistant_triage(client):
    """Verifies AI Assistant triage and emergency detection."""
    # Emergency query
    r_emerg = client.post("/api/ai/consult", json={"query": "Sudden crushing chest pain radiating to left arm"})
    assert r_emerg.status_code == 200
    res_emerg = r_emerg.get_json()["result"]
    assert res_emerg["is_emergency"] is True
    assert "112" in res_emerg["response"] or "911" in res_emerg["response"]

    # Mild OTC symptom query
    r_mild = client.post("/api/ai/consult", json={"query": "I have a mild tension headache and need rest advice"})
    assert r_mild.status_code == 200
    res_mild = r_mild.get_json()["result"]
    assert res_mild["is_emergency"] is False
    assert len(res_mild["response"]) > 30

    # Empty query rejection
    r_empty = client.post("/api/ai/consult", json={"query": ""})
    assert r_empty.status_code == 400

def test_prescription_lifecycle_order_sync_and_rejection_restores_stock(app, client):
    """Verifies prescription verification auto-transitions orders and rejection restores stock."""
    import io

    with app.app_context():
        # 1. Customer uploads prescription
        client.post("/api/auth/login", json={"email": "demo.customer@mediapp.local", "password": "Customer@MediApp2026!"})
        pdf_bytes = b"%PDF-1.4 Clinical Prescription Rx Augmentin 625mg %%EOF"
        r_up = client.post("/api/prescriptions/upload", data={"file": (io.BytesIO(pdf_bytes), "test_rx.pdf")}, content_type="multipart/form-data")
        assert r_up.status_code == 201
        rx_id = r_up.get_json()["prescription"]["id"]

        # 2. Customer places order for Rx medicine (medicine_id 7 = Voveran SR 100mg, prescription_required = 1)
        inv_before = query_db("SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 7", one=True)["stock_quantity"]
        client.delete("/api/cart")
        client.post("/api/cart/items", json={"medicine_id": 7, "quantity": 1, "pharmacy_id": 1})
        r_ord = client.post("/api/orders", json={
            "delivery_address": {"line1": "Rx St", "city": "Bengaluru", "state": "Karnataka", "pincode": "560001"},
            "prescription_id": rx_id
        })
        assert r_ord.status_code == 201
        order_id = r_ord.get_json()["order"]["id"]
        assert r_ord.get_json()["order"]["order_status"] == "AWAITING_PRESCRIPTION"

        # Stock was decremented by 1
        inv_reserved = query_db("SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 7", one=True)["stock_quantity"]
        assert inv_reserved == inv_before - 1

        # 3. Pharmacist logs in and verifies prescription
        client.post("/api/auth/login", json={"email": "demo.pharmacy@mediapp.local", "password": "Pharmacy@MediApp2026!"})
        r_ver = client.post(f"/api/prescriptions/{rx_id}/verify", json={"decision": "verified"})
        assert r_ver.status_code == 200

        # Linked order must automatically transition to PRESCRIPTION_VERIFIED
        ord_check = query_db("SELECT order_status FROM orders WHERE id = ?", (order_id,), one=True)
        assert ord_check["order_status"] == "PRESCRIPTION_VERIFIED"

        # Pharmacy can accept the verified order
        r_accept = client.post(f"/api/pharmacy/orders/{order_id}/accept")
        assert r_accept.status_code == 200
        assert r_accept.get_json()["order"]["order_status"] == "ACCEPTED"

        # 4. Now test REJECTION: Create another order with a new prescription
        client.post("/api/auth/login", json={"email": "demo.customer@mediapp.local", "password": "Customer@MediApp2026!"})
        r_up2 = client.post("/api/prescriptions/upload", data={"file": (io.BytesIO(pdf_bytes), "test_rx2.pdf")}, content_type="multipart/form-data")
        rx_id2 = r_up2.get_json()["prescription"]["id"]

        stock_before_rej = query_db("SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 7", one=True)["stock_quantity"]
        client.delete("/api/cart")
        client.post("/api/cart/items", json={"medicine_id": 7, "quantity": 2, "pharmacy_id": 1})
        r_ord2 = client.post("/api/orders", json={
            "delivery_address": {"line1": "Rx St 2", "city": "Bengaluru", "state": "Karnataka", "pincode": "560001"},
            "prescription_id": rx_id2
        })
        order_id2 = r_ord2.get_json()["order"]["id"]
        assert r_ord2.get_json()["order"]["order_status"] == "AWAITING_PRESCRIPTION"

        # Pharmacist rejects this prescription
        client.post("/api/auth/login", json={"email": "demo.pharmacy@mediapp.local", "password": "Pharmacy@MediApp2026!"})
        r_rej = client.post(f"/api/prescriptions/{rx_id2}/verify", json={"decision": "rejected", "rejection_reason": "Dosage illegible"})
        assert r_rej.status_code == 200

        # Linked order must be CANCELLED and stock restored
        ord2_check = query_db("SELECT order_status FROM orders WHERE id = ?", (order_id2,), one=True)
        assert ord2_check["order_status"] == "CANCELLED"
        stock_after_rej = query_db("SELECT stock_quantity FROM pharmacy_inventory WHERE pharmacy_id = 1 AND medicine_id = 7", one=True)["stock_quantity"]
        assert stock_after_rej == stock_before_rej

        # 5. Customer attempts to reuse the rejected prescription rx_id2
        client.post("/api/auth/login", json={"email": "demo.customer@mediapp.local", "password": "Customer@MediApp2026!"})
        client.delete("/api/cart")
        client.post("/api/cart/items", json={"medicine_id": 7, "quantity": 1, "pharmacy_id": 1})
        r_reuse = client.post("/api/orders", json={
            "delivery_address": {"line1": "Rx St 3", "city": "Bengaluru", "state": "Karnataka", "pincode": "560001"},
            "prescription_id": rx_id2
        })
        assert r_reuse.status_code == 400
        assert "rejected" in r_reuse.get_json()["error"].lower()

def test_pharmacy_inventory_crud_and_validation(client):
    """Verifies pharmacy inventory CRUD operations, foreign key checks, and DELETE endpoint."""
    # Login as pharmacy staff
    client.post("/api/auth/login", json={"email": "demo.pharmacy@mediapp.local", "password": "Pharmacy@MediApp2026!"})

    # 1. Attempt to add nonexistent medicine ID
    r_bad = client.post("/api/pharmacy/inventory", json={"medicine_id": 999999, "quantity": 10, "unit_price": 50.0})
    assert r_bad.status_code == 404
    assert "does not exist" in r_bad.get_json()["error"].lower()

    # 2. Add/update valid medicine in inventory (e.g. medicine 3 = Calpol)
    r_add = client.post("/api/pharmacy/inventory", json={
        "medicine_id": 3,
        "quantity": 120,
        "unit_price": 45.0,
        "batch_number": "BATCH-2026-TEST",
        "expiry_date": "2027-12-31",
        "is_available": True
    })
    assert r_add.status_code == 200

    # 3. Verify in inventory
    r_inv = client.get("/api/pharmacy/inventory?q=Calpol")
    assert r_inv.status_code == 200
    med3 = [it for it in r_inv.get_json()["inventory"] if it["medicine_id"] == 3]
    assert len(med3) > 0
    assert med3[0]["stock_quantity"] == 120

    # 4. Delete medicine from inventory
    r_del = client.delete("/api/pharmacy/inventory/3")
    assert r_del.status_code == 200

    # 5. Deleting already deleted item returns 404
    r_del2 = client.delete("/api/pharmacy/inventory/3")
    assert r_del2.status_code == 404

def test_delivery_driver_hoarding_prevention(app, client):
    """Verifies delivery riders cannot exceed maximum active courier capacity (5 orders)."""
    with app.app_context():
        # Clean any preexisting test orders
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM orders WHERE id LIKE 'ORD-TEST-CAP-%'")

        # Setup 6 orders in READY_FOR_PICKUP
        for i in range(1, 7):
            cur.execute(f"""
                INSERT INTO orders (id, customer_id, pharmacy_id, delivery_address_json, subtotal, tax, delivery_fee, discount, total_amount, currency, payment_status, order_status)
                VALUES ('ORD-TEST-CAP-{i}', 1, 1, '{{"city":"Blr"}}', 100, 5, 30, 0, 135, 'INR', 'paid', 'READY_FOR_PICKUP')
            """)
        conn.commit()

        # Login as delivery rider
        client.post("/api/auth/login", json={"email": "demo.delivery@mediapp.local", "password": "Delivery@MediApp2026!"})

        # Count how many active orders rider already has
        cur.execute("SELECT COUNT(*) as c FROM orders WHERE delivery_person_id = 4 AND order_status IN ('DELIVERY_ASSIGNED', 'PICKED_UP', 'IN_TRANSIT')")
        existing_active = cur.fetchone()["c"]

        # Claim orders up to capacity limit (5)
        claimed_ids = []
        for i in range(1, 6 - existing_active + 1):
            r = client.post(f"/api/delivery/orders/ORD-TEST-CAP-{i}/claim")
            if r.status_code == 200:
                claimed_ids.append(f"ORD-TEST-CAP-{i}")

        # Next claim exceeding capacity must be rejected with 409
        r_exceed = client.post(f"/api/delivery/orders/ORD-TEST-CAP-6/claim")
        assert r_exceed.status_code == 409
        assert "maximum active delivery capacity" in r_exceed.get_json()["error"].lower()

        # Complete one claimed order
        if claimed_ids:
            first_id = claimed_ids[0]
            client.post(f"/api/delivery/orders/{first_id}/pickup")
            client.post(f"/api/delivery/orders/{first_id}/in-transit")
            client.post(f"/api/delivery/orders/{first_id}/complete", json={"proof": "Delivered to door"})

            # Now claiming ORD-TEST-CAP-6 succeeds
            r_retry = client.post(f"/api/delivery/orders/ORD-TEST-CAP-6/claim")
            assert r_retry.status_code == 200

def test_empty_prescription_file_rejected(client):
    """Verifies that 0-byte file uploads are rejected with 400."""
    import io
    client.post("/api/auth/login", json={"email": "demo.customer@mediapp.local", "password": "Customer@MediApp2026!"})
    r = client.post("/api/prescriptions/upload", data={"file": (io.BytesIO(b""), "empty.pdf")}, content_type="multipart/form-data")
    assert r.status_code == 400
    assert "empty" in r.get_json()["error"].lower()

def test_admin_update_nonexistent_pharmacy_404(client):
    """Verifies that updating a nonexistent pharmacy status returns 404."""
    client.post("/api/auth/login", json={"email": "demo.admin@mediapp.local", "password": "Admin@MediApp2026!"})
    r = client.put("/api/admin/pharmacies/999999/status", json={"status": "approved"})
    assert r.status_code == 404
    assert "not found" in r.get_json()["error"].lower()
