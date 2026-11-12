"""
Integration tests for order placement, cart management, and cross-portal shared order identity.
"""
def test_order_creation_from_cart(auth_client):
    client = auth_client("customer")

    # Add item to cart
    add_res = client.post("/api/cart/items", json={"medicine_id": 2, "quantity": 2, "pharmacy_id": 1})
    assert add_res.status_code == 200

    # Get cart
    cart_res = client.get("/api/cart")
    assert cart_res.status_code == 200
    assert cart_res.json["item_count"] >= 2

    # Place order
    order_payload = {
        "delivery_address": {
            "line1": "Flat 101, Test Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560001",
            "recipient_phone": "+91 9999888822"
        },
        "delivery_notes": "Call upon arrival"
    }
    create_res = client.post("/api/orders", json=order_payload)
    assert create_res.status_code == 201
    order = create_res.json["order"]
    order_id = order["id"]

    # Verify ID is a stable formatted string (not an integer)
    assert isinstance(order_id, str)
    assert order_id.startswith("ORD-")
    assert order["total_amount"] > 0
    assert len(order["items"]) >= 1

    # Verify same order is accessible via direct order endpoint
    detail_res = client.get(f"/api/orders/{order_id}")
    assert detail_res.status_code == 200
    assert detail_res.json["order"]["id"] == order_id
    assert detail_res.json["order"]["total_amount"] == order["total_amount"]

def test_order_isolation_prevents_idor(client, auth_client):
    # Customer 1 creates an order
    cust1 = auth_client("customer")
    cust1.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1, "pharmacy_id": 1})
    res = cust1.post("/api/orders", json={
        "delivery_address": {"line1": "Private Suite", "city": "Bengaluru", "state": "KA", "pincode": "560001"}
    })
    order_id = res.json["order"]["id"]

    # Switch to delivery rider (unassigned)
    deliv = auth_client("delivery")
    idor_res = deliv.get(f"/api/orders/{order_id}")
    # Delivery rider cannot access private customer order unless ready for pickup / assigned
    # Initially order is PLACED, so delivery rider is rejected with 403
    assert idor_res.status_code == 403


def test_customer_cross_order_cancellation_prevented_idor(app):
    """BOLA/IDOR: Customer 2 must not be able to cancel Customer 1's order."""
    cust1 = app.test_client()
    cust2 = app.test_client()

    cust1.post("/api/auth/demo-login", json={"role": "customer"})
    cust2.post("/api/auth/register", json={
        "email": "attacker.customer@example.com",
        "password": "Password123!",
        "full_name": "Attacker User",
        "phone": "+91 9111122222"
    })

    cust1.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1, "pharmacy_id": 1})
    res1 = cust1.post("/api/orders", json={
        "delivery_address": {"line1": "Victim Address", "city": "Bengaluru", "state": "KA", "pincode": "560001"}
    })
    assert res1.status_code == 201
    victim_order_id = res1.json["order"]["id"]

    # Attacker attempts to cancel victim's order
    cancel_attempt = cust2.post(f"/api/orders/{victim_order_id}/cancel", json={
        "reason": "Malicious cancellation attempt"
    })
    assert cancel_attempt.status_code == 403
    assert "Access denied. You do not own this order." in cancel_attempt.json["error"]


def test_customer_cannot_arbitrarily_transition_order(app):
    """Customer cannot invoke status transition endpoint directly to mark order DELIVERED."""
    cust = app.test_client()
    cust.post("/api/auth/demo-login", json={"role": "customer"})

    cust.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1, "pharmacy_id": 1})
    res = cust.post("/api/orders", json={
        "delivery_address": {"line1": "Customer Address", "city": "Bengaluru", "state": "KA", "pincode": "560001"}
    })
    order_id = res.json["order"]["id"]

    # Customer attempts to jump state to DELIVERED
    jump_res = cust.post(f"/api/orders/{order_id}/transition", json={"target_status": "DELIVERED"})
    assert jump_res.status_code in (400, 403)
    assert "Invalid transition" in jump_res.json["error"] or "not authorized" in jump_res.json["error"].lower()


def test_pharmacy_cannot_accept_order_of_different_store(app):
    """Pharmacy isolation: Pharmacist from Pharmacy 1 cannot accept order for Pharmacy 2."""
    cust = app.test_client()
    cust.post("/api/auth/demo-login", json={"role": "customer"})

    # Order from Pharmacy 2
    cust.post("/api/cart/items", json={"medicine_id": 2, "quantity": 1, "pharmacy_id": 2, "clear_existing": True})
    order_res = cust.post("/api/orders", json={
        "delivery_address": {"line1": "Customer Address", "city": "Bengaluru", "state": "KA", "pincode": "560001"}
    })
    order_id = order_res.json["order"]["id"]

    # Pharmacy 1 logs in
    pharm1 = app.test_client()
    pharm1.post("/api/auth/demo-login", json={"role": "pharmacy"})

    # Pharmacy 1 tries to accept Pharmacy 2's order
    accept_res = pharm1.post(f"/api/pharmacy/orders/{order_id}/accept")
    assert accept_res.status_code == 403
    assert "Order belongs to another pharmacy" in accept_res.json["error"]


def test_payment_rejected_on_cancelled_order(app):
    """Payments cannot be initiated or completed on a CANCELLED order."""
    cust = app.test_client()
    cust.post("/api/auth/demo-login", json={"role": "customer"})

    cust.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1, "pharmacy_id": 1, "clear_existing": True})
    res = cust.post("/api/orders", json={
        "delivery_address": {"line1": "Test Address", "city": "Bengaluru", "state": "KA", "pincode": "560001"}
    })
    order_id = res.json["order"]["id"]

    # Customer cancels order
    c_res = cust.post(f"/api/orders/{order_id}/cancel", json={"reason": "Changed mind"})
    assert c_res.status_code == 200

    # Attempt to initiate payment
    pay_init = cust.post("/api/payments/create-order", json={"order_id": order_id})
    assert pay_init.status_code == 400
    assert "cancelled order" in pay_init.json["error"].lower()

    # Attempt to verify payment
    pay_verify = cust.post("/api/payments/verify", json={"order_id": order_id, "status": "success"})
    assert pay_verify.status_code == 400
    assert "cancelled order" in pay_verify.json["error"].lower()


def test_delivery_claim_concurrency(app):
    """Only one delivery courier can claim an order; the second claim must be rejected."""
    cust = app.test_client()
    pharm = app.test_client()
    rider1 = app.test_client()
    rider2 = app.test_client()

    cust.post("/api/auth/demo-login", json={"role": "customer"})
    pharm.post("/api/auth/demo-login", json={"role": "pharmacy"})
    rider1.post("/api/auth/demo-login", json={"role": "delivery"})
    rider2.post("/api/auth/register", json={
        "email": "rider2.concurrent@example.com",
        "password": "Password123!",
        "full_name": "Rider Two",
        "phone": "+91 9333344444"
    })
    # Switch rider2 or promote rider2
    from app.database import get_db
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = 'rider2.concurrent@example.com'")
        u2 = cur.fetchone()
        cur.execute("UPDATE users SET role = 'delivery' WHERE id = ?", (u2["id"],))
        cur.execute("""
            INSERT INTO delivery_profiles (user_id, vehicle_type, vehicle_number, driving_license, is_available, status)
            VALUES (?, 'Motorcycle', 'KA-01-XY-9999', 'DL9999999999', 1, 'approved')
        """, (u2["id"],))
        conn.commit()

    # Re-login rider2
    rider2.post("/api/auth/login", json={"email": "rider2.concurrent@example.com", "password": "Password123!"})

    # Customer orders and pays
    cust.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1, "pharmacy_id": 1, "clear_existing": True})
    order_res = cust.post("/api/orders", json={
        "delivery_address": {"line1": "Speedy St", "city": "Bengaluru", "state": "KA", "pincode": "560001"}
    })
    order_id = order_res.json["order"]["id"]
    cust.post("/api/payments/verify", json={"order_id": order_id, "status": "success"})

    # Pharmacy prepares and marks ready
    pharm.post(f"/api/pharmacy/orders/{order_id}/accept")
    pharm.post(f"/api/orders/{order_id}/transition", json={"target_status": "PREPARING", "notes": "Packaging medicines"})
    pharm.post(f"/api/orders/{order_id}/transition", json={"target_status": "READY_FOR_PICKUP", "notes": "Ready for courier"})

    # Rider 1 claims
    claim1 = rider1.post(f"/api/delivery/orders/{order_id}/claim")
    assert claim1.status_code == 200
    assert claim1.json["order"]["delivery_person_id"] is not None

    # Rider 2 claims immediately after
    claim2 = rider2.post(f"/api/delivery/orders/{order_id}/claim")
    assert claim2.status_code in (400, 409)
    assert "claimed" in claim2.json["error"].lower()
