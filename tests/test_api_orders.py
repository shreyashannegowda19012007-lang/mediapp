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
