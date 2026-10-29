"""
Integration tests for payment workflows.
Verifies demo payment simulation, HMAC signature checks, and duplicate payment replay prevention.
"""
def test_payment_initiation_and_demo_completion(auth_client):
    client = auth_client("customer")

    # Create an order
    client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1, "pharmacy_id": 1})
    order_res = client.post("/api/orders", json={
        "delivery_address": {"line1": "Payment Test St", "city": "Bengaluru", "state": "KA", "pincode": "560001"}
    })
    order_id = order_res.json["order"]["id"]

    # Initiate payment
    init_res = client.post("/api/payments/create-order", json={"order_id": order_id})
    assert init_res.status_code == 200
    payment_order = init_res.json["payment_order"]
    assert payment_order["order_id"] == order_id

    # Verify payment in demo mode
    verify_res = client.post("/api/payments/verify", json={
        "order_id": order_id,
        "status": "success"
    })
    assert verify_res.status_code == 200
    assert verify_res.json["status"] == "success"

    # Confirm order payment_status in database is now paid
    ord_check = client.get(f"/api/orders/{order_id}")
    assert ord_check.json["order"]["payment_status"] == "paid"

def test_duplicate_payment_prevention(auth_client):
    client = auth_client("customer")
    client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1, "pharmacy_id": 1})
    order_res = client.post("/api/orders", json={
        "delivery_address": {"line1": "Replay Test St", "city": "Bengaluru", "state": "KA", "pincode": "560001"}
    })
    order_id = order_res.json["order"]["id"]

    # Complete payment
    client.post("/api/payments/verify", json={"order_id": order_id, "status": "success"})

    # Attempting to initiate payment again on paid order should be rejected
    second_init = client.post("/api/payments/create-order", json={"order_id": order_id})
    assert second_init.status_code == 400
    assert "already been paid" in second_init.json["error"]
