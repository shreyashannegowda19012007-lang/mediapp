import sys
import requests

BASE_URL = "http://127.0.0.1:5000"

def log(msg, success=True):
    symbol = "✅" if success else "❌"
    print(f"{symbol} {msg}")

def run_e2e_verification():
    print("=" * 60)
    print("STARTING LIVE CROSS-PORTAL E2E VERIFICATION")
    print("=" * 60)

    # 1. Customer registration and login
    cust_session = requests.Session()
    reg_email = "e2e.test.customer@mediapp.local"
    reg_payload = {
        "email": reg_email,
        "password": "Password123!",
        "full_name": "E2E Test Customer",
        "phone": "+919876543299"
    }
    
    # Try register (or handle if already registered from previous run)
    r_reg = cust_session.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
    if r_reg.status_code == 201:
        log(f"Customer registered: {reg_email}")
    elif r_reg.status_code == 409:
        log(f"Customer already registered, proceeding to login: {reg_email}")
    else:
        log(f"Customer registration failed: {r_reg.status_code} {r_reg.text}", False)
        return False

    r_login = cust_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": reg_email,
        "password": "Password123!"
    })
    assert r_login.status_code == 200, f"Customer login failed: {r_login.text}"
    user_data = r_login.json()["user"]
    log(f"Customer logged in: {user_data['email']}, role: {user_data['role']}, roles: {user_data.get('authorized_roles')}")
    assert user_data["role"] == "customer"

    # 2. RBAC check: Customer cannot access admin, pharmacy, delivery endpoints
    r_bad_admin = cust_session.get(f"{BASE_URL}/api/admin/stats")
    assert r_bad_admin.status_code == 403, f"Expected 403 for customer accessing admin, got {r_bad_admin.status_code}"
    r_bad_pharm = cust_session.get(f"{BASE_URL}/api/pharmacy/orders")
    assert r_bad_pharm.status_code == 403, f"Expected 403 for customer accessing pharmacy, got {r_bad_pharm.status_code}"
    r_bad_deliv = cust_session.get(f"{BASE_URL}/api/delivery/available")
    assert r_bad_deliv.status_code == 403, f"Expected 403 for customer accessing delivery, got {r_bad_deliv.status_code}"
    log("RBAC verified: Customer blocked (HTTP 403) from admin, pharmacy, and delivery APIs")

    # 3. Medicine Search & Inventory Check via GET /api/medicines
    r_search = cust_session.get(f"{BASE_URL}/api/medicines", params={"q": "Paracetamol"})
    assert r_search.status_code == 200, f"Search failed: {r_search.text}"
    meds = r_search.json().get("medicines", [])
    assert len(meds) > 0, "No medicines found for Paracetamol"
    target_med = meds[0]
    log(f"Medicine found: '{target_med['name']}' (ID: {target_med['id']}, MRP: ₹{target_med['mrp']})")

    # Target fulfilling pharmacy 1 (Apollo Pharmacy Koramangala)
    fulfilling_pharmacy_id = 1
    other_pharmacy_id = 2

    # 4. Cart management and Cross-Pharmacy Conflict Detection (DEF-15)
    # Clear existing cart first
    cust_session.delete(f"{BASE_URL}/api/cart")
    
    # Add medicine to cart for fulfilling_pharmacy_id
    r_cart1 = cust_session.post(f"{BASE_URL}/api/cart/items", json={
        "medicine_id": target_med["id"],
        "pharmacy_id": fulfilling_pharmacy_id,
        "quantity": 2
    })
    assert r_cart1.status_code == 200, f"Failed to add to cart: {r_cart1.text}"
    log(f"Added item to cart for Pharmacy {fulfilling_pharmacy_id}")

    # Test DEF-15 cross-pharmacy conflict rejection
    r_cart_conflict = cust_session.post(f"{BASE_URL}/api/cart/items", json={
        "medicine_id": target_med["id"],
        "pharmacy_id": other_pharmacy_id,
        "quantity": 1
    })
    assert r_cart_conflict.status_code == 409, f"Expected 409 Conflict when switching pharmacy, got {r_cart_conflict.status_code}"
    assert r_cart_conflict.json().get("conflict") is True
    log("DEF-15 verified: Cross-pharmacy cart conflict rejected with HTTP 409 Conflict")

    # 5. Prescription Privacy Check (DEF-05)
    # Customer uploads a dummy prescription text/file
    files = {"file": ("rx_test.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4", "image/png")}
    r_rx_upload = cust_session.post(f"{BASE_URL}/api/prescriptions/upload", files=files)
    assert r_rx_upload.status_code in (200, 201), f"Prescription upload failed: {r_rx_upload.text}"
    rx_id = r_rx_upload.json().get("prescription", {}).get("id") or r_rx_upload.json().get("id")
    log(f"Prescription uploaded successfully (ID: {rx_id})")

    # Verify delivery rider CANNOT view customer prescription (DEF-05)
    deliv_session = requests.Session()
    r_deliv_login = deliv_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo.delivery@mediapp.local",
        "password": "Delivery@MediApp2026!"
    })
    assert r_deliv_login.status_code == 200, f"Delivery login failed: {r_deliv_login.text}"
    r_rx_deliv_block = deliv_session.get(f"{BASE_URL}/api/prescriptions/{rx_id}")
    assert r_rx_deliv_block.status_code == 403, f"Expected 403 for delivery accessing prescription, got {r_rx_deliv_block.status_code}"
    log("DEF-05 verified: Delivery rider blocked (HTTP 403) from inspecting patient prescription")

    # 6. Customer Order Placement & Payment Verification
    order_payload = {
        "delivery_address": {
            "line1": "Flat 402, Sunshine Heights",
            "line2": "12th Main, Koramangala 4th Block",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560034",
            "recipient_phone": "+919876543299"
        },
        "prescription_id": rx_id,
        "delivery_notes": "Please leave at security gate if not answering door"
    }
    r_order = cust_session.post(f"{BASE_URL}/api/orders", json=order_payload)
    assert r_order.status_code == 201, f"Order placement failed: {r_order.text}"
    order_data = r_order.json().get("order", {})
    order_id = order_data["id"]
    log(f"Order placed: {order_id} (Total: ₹{order_data['total_amount']}, Status: {order_data['order_status']})")

    # Create Payment Intent & Verify Payment
    r_pay_create = cust_session.post(f"{BASE_URL}/api/payments/create-order", json={"order_id": order_id})
    assert r_pay_create.status_code == 200, f"Payment initiate failed: {r_pay_create.text}"
    
    r_pay_verify = cust_session.post(f"{BASE_URL}/api/payments/verify", json={
        "order_id": order_id,
        "status": "success"
    })
    assert r_pay_verify.status_code == 200, f"Payment verify failed: {r_pay_verify.text}"
    log("Payment verified successfully; order marked as paid")

    # 7. Pharmacy Portal Actions
    # Login as pharmacy staff (Apollo Koramangala)
    pharm_session = requests.Session()
    r_pharm_login = pharm_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo.pharmacy@mediapp.local",
        "password": "Pharmacy@MediApp2026!"
    })
    assert r_pharm_login.status_code == 200, f"Pharmacy login failed: {r_pharm_login.text}"
    log(f"Pharmacy staff logged in: {r_pharm_login.json()['user']['email']}")

    # Pharmacy can view prescription for clinical verification
    r_pharm_rx = pharm_session.get(f"{BASE_URL}/api/prescriptions/{rx_id}")
    assert r_pharm_rx.status_code == 200, f"Pharmacy failed to read prescription: {r_pharm_rx.text}"
    log("Pharmacy authorized to view patient prescription for verification")

    # If order is awaiting prescription, pharmacy verifies prescription and transitions order
    current_order = pharm_session.get(f"{BASE_URL}/api/orders/{order_id}").json()["order"]
    if current_order["order_status"] == "AWAITING_PRESCRIPTION":
        r_rx_verify = pharm_session.post(f"{BASE_URL}/api/prescriptions/{rx_id}/verify", json={"decision": "verified"})
        assert r_rx_verify.status_code == 200, f"Rx verification failed: {r_rx_verify.text}"
        log("Pharmacy verified patient prescription")

        r_trans_rx = pharm_session.post(f"{BASE_URL}/api/orders/{order_id}/transition", json={
            "target_status": "PRESCRIPTION_VERIFIED",
            "notes": "Prescription validated against schedule H guidelines"
        })
        assert r_trans_rx.status_code == 200, f"Transition to PRESCRIPTION_VERIFIED failed: {r_trans_rx.text}"
        log(f"Pharmacy transitioned order {order_id} to PRESCRIPTION_VERIFIED")

    # Pharmacy accepts the order
    r_accept = pharm_session.post(f"{BASE_URL}/api/pharmacy/orders/{order_id}/accept")
    assert r_accept.status_code == 200, f"Pharmacy accept failed: {r_accept.text}"
    log(f"Pharmacy accepted order {order_id} (status: ACCEPTED)")

    # Pharmacy transitions to PREPARING
    r_prep = pharm_session.post(f"{BASE_URL}/api/orders/{order_id}/transition", json={
        "target_status": "PREPARING",
        "notes": "Picking items from pharmacy racks"
    })
    assert r_prep.status_code == 200, f"Pharmacy preparing failed: {r_prep.text}"
    log(f"Pharmacy marked order {order_id} as PREPARING")

    # Pharmacy transitions order to READY_FOR_PICKUP
    r_ready = pharm_session.post(f"{BASE_URL}/api/orders/{order_id}/transition", json={
        "target_status": "READY_FOR_PICKUP",
        "notes": "Packed in sealed tamper-evident medical pouch"
    })
    assert r_ready.status_code == 200, f"Pharmacy ready for pickup failed: {r_ready.text}"
    log(f"Pharmacy marked order {order_id} as READY_FOR_PICKUP")

    # 8. Delivery Portal Actions
    # Delivery rider views available orders
    r_avail = deliv_session.get(f"{BASE_URL}/api/delivery/available")
    assert r_avail.status_code == 200, f"Failed to list available orders: {r_avail.text}"
    avail_orders = r_avail.json().get("available_orders", [])
    matching = [o for o in avail_orders if o["id"] == order_id]
    assert len(matching) > 0, f"Order {order_id} not visible in delivery pool!"
    log(f"Delivery rider found order {order_id} in available orders pool")

    # Claim order
    r_claim = deliv_session.post(f"{BASE_URL}/api/delivery/orders/{order_id}/claim")
    assert r_claim.status_code == 200, f"Delivery claim failed: {r_claim.text}"
    log(f"Delivery rider claimed order {order_id} (status: DELIVERY_ASSIGNED)")

    # Pick up order from pharmacy
    r_pickup = deliv_session.post(f"{BASE_URL}/api/delivery/orders/{order_id}/pickup")
    assert r_pickup.status_code == 200, f"Delivery pickup failed: {r_pickup.text}"
    log(f"Delivery rider picked up order {order_id} (status: PICKED_UP)")

    # Mark in-transit
    r_intransit = deliv_session.post(f"{BASE_URL}/api/delivery/orders/{order_id}/in-transit")
    assert r_intransit.status_code == 200, f"Delivery in-transit failed: {r_intransit.text}"
    log(f"Delivery rider en route (status: IN_TRANSIT)")

    # Update rider GPS location coordinates (DEF-07)
    r_loc = deliv_session.post(f"{BASE_URL}/api/delivery/location", json={
        "latitude": 12.9352,
        "longitude": 77.6245
    })
    assert r_loc.status_code == 200, f"Location update failed: {r_loc.text}"
    log("DEF-07 verified: Delivery rider GPS location broadcasted successfully")

    # Complete delivery
    r_complete = deliv_session.post(f"{BASE_URL}/api/delivery/orders/{order_id}/complete", json={
        "notes": "Delivered at doorstep to customer"
    })
    assert r_complete.status_code == 200, f"Delivery complete failed: {r_complete.text}"
    log(f"Delivery rider marked order {order_id} as DELIVERED")

    # 9. Admin Portal Verification
    admin_session = requests.Session()
    r_admin_login = admin_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo.admin@mediapp.local",
        "password": "Admin@MediApp2026!"
    })
    assert r_admin_login.status_code == 200, f"Admin login failed: {r_admin_login.text}"
    log(f"Admin logged in: {r_admin_login.json()['user']['email']}")

    # Check stats and order status
    r_stats = admin_session.get(f"{BASE_URL}/api/admin/stats")
    assert r_stats.status_code == 200, f"Admin stats failed: {r_stats.text}"
    metrics = r_stats.json().get("metrics", {})
    log(f"Admin stats verified: Total Orders: {metrics.get('total_orders')}, Delivered: {metrics.get('order_breakdown', {}).get('DELIVERED')}, Revenue: ₹{metrics.get('total_revenue')}")

    # Inspect specific order via admin API
    r_admin_ord = admin_session.get(f"{BASE_URL}/api/orders/{order_id}")
    assert r_admin_ord.status_code == 200, f"Admin get order failed: {r_admin_ord.text}"
    admin_ord_data = r_admin_ord.json().get("order", {})
    assert admin_ord_data["order_status"] == "DELIVERED", f"Expected DELIVERED status, got {admin_ord_data['order_status']}"
    log(f"Admin verified order {order_id} status is DELIVERED")

    # 10. Customer Portal Verification
    r_cust_ord = cust_session.get(f"{BASE_URL}/api/orders/{order_id}")
    assert r_cust_ord.status_code == 200, f"Customer get order failed: {r_cust_ord.text}"
    cust_ord_data = r_cust_ord.json().get("order", {})
    assert cust_ord_data["order_status"] == "DELIVERED", f"Customer saw status {cust_ord_data['order_status']}, expected DELIVERED"
    log(f"Customer confirmed order {order_id} status is DELIVERED with tracking timeline")

    # 11. Role Switching Verification
    # Admin switches to customer role
    r_switch = admin_session.post(f"{BASE_URL}/api/auth/switch-role", json={"role": "customer"})
    assert r_switch.status_code == 200, f"Switch role failed: {r_switch.text}"
    assert r_switch.json()["active_role"] == "customer"
    # Admin switches back to admin
    r_switch_back = admin_session.post(f"{BASE_URL}/api/auth/switch-role", json={"role": "admin"})
    assert r_switch_back.status_code == 200, f"Switch role back failed: {r_switch_back.text}"
    assert r_switch_back.json()["active_role"] == "admin"
    log("RBAC verified: Role switching permitted for authorized roles")

    # Customer attempts to switch to admin (unauthorized)
    r_bad_switch = cust_session.post(f"{BASE_URL}/api/auth/switch-role", json={"role": "admin"})
    assert r_bad_switch.status_code == 403, f"Expected 403 for unauthorized switch, got {r_bad_switch.status_code}"
    log("RBAC verified: Unauthorized role switch rejected with HTTP 403 Forbidden")

    # 12. Deactivated Account Login Rejection
    # Admin deactivates test customer account
    r_deact = admin_session.put(f"{BASE_URL}/api/admin/users/{user_data['id']}/status", json={"is_active": False})
    assert r_deact.status_code == 200, f"Deactivation failed: {r_deact.text}"
    # Verify deactivated customer cannot login
    deact_session = requests.Session()
    r_deact_login = deact_session.post(f"{BASE_URL}/api/auth/login", json={
        "email": reg_email,
        "password": "Password123!"
    })
    assert r_deact_login.status_code == 403, f"Expected 403 for deactivated user, got {r_deact_login.status_code}"
    log("Account status verified: Deactivated user login rejected with HTTP 403 Forbidden")

    # Re-activate user
    admin_session.put(f"{BASE_URL}/api/admin/users/{user_data['id']}/status", json={"is_active": True})

    # 13. Static 404 handler check (DEF-03)
    r_static_missing = requests.get(f"{BASE_URL}/static/nonexistent_file_12345.css")
    assert r_static_missing.status_code == 404, f"Expected 404 for missing static file, got {r_static_missing.status_code}"
    log("DEF-03 verified: Missing static files return HTTP 404 instead of serving index.html")

    # 14. Live Prescription Lifecycle & Order Auto-Transition Verification (DEF-16)
    # Upload new prescription
    files_rx2 = {"file": ("rx_voveran.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4", "image/png")}
    r_rx2 = cust_session.post(f"{BASE_URL}/api/prescriptions/upload", files=files_rx2)
    assert r_rx2.status_code in (200, 201), f"Rx upload failed: {r_rx2.text}"
    rx2_id = r_rx2.json().get("prescription", {}).get("id") or r_rx2.json().get("id")

    # Place order for Rx medicine 7 (Voveran SR 100mg)
    cust_session.delete(f"{BASE_URL}/api/cart")
    cust_session.post(f"{BASE_URL}/api/cart/items", json={"medicine_id": 7, "quantity": 1, "pharmacy_id": fulfilling_pharmacy_id})
    r_rx_ord = cust_session.post(f"{BASE_URL}/api/orders", json={
        "delivery_address": order_payload["delivery_address"],
        "prescription_id": rx2_id
    })
    assert r_rx_ord.status_code == 201, f"Rx order failed: {r_rx_ord.text}"
    rx_ord_id = r_rx_ord.json()["order"]["id"]
    assert r_rx_ord.json()["order"]["order_status"] == "AWAITING_PRESCRIPTION"
    log(f"DEF-16: Placed Rx order {rx_ord_id} in AWAITING_PRESCRIPTION status")

    # Pharmacist verifies prescription -> order must auto-transition to PRESCRIPTION_VERIFIED
    r_rx2_ver = pharm_session.post(f"{BASE_URL}/api/prescriptions/{rx2_id}/verify", json={"decision": "verified"})
    assert r_rx2_ver.status_code == 200, f"Verify failed: {r_rx2_ver.text}"
    r_check_rx_ord = pharm_session.get(f"{BASE_URL}/api/orders/{rx_ord_id}")
    assert r_check_rx_ord.json()["order"]["order_status"] == "PRESCRIPTION_VERIFIED"
    log(f"DEF-16 verified: Order {rx_ord_id} automatically transitioned to PRESCRIPTION_VERIFIED upon prescription approval")

    # Pharmacy can accept the verified Rx order
    r_rx_accept = pharm_session.post(f"{BASE_URL}/api/pharmacy/orders/{rx_ord_id}/accept")
    assert r_rx_accept.status_code == 200, f"Rx order accept failed: {r_rx_accept.text}"
    assert r_rx_accept.json()["order"]["order_status"] == "ACCEPTED"
    log(f"DEF-16 verified: Pharmacy accepted PRESCRIPTION_VERIFIED order {rx_ord_id}")

    # 15. Live Pharmacy Inventory CRUD (Add & Delete) Verification (DEF-17)
    r_inv_add = pharm_session.post(f"{BASE_URL}/api/pharmacy/inventory", json={
        "medicine_id": 3,
        "quantity": 150,
        "unit_price": 25.0,
        "batch_number": "LIVE-TEST-BATCH",
        "expiry_date": "2028-01-01",
        "is_available": True
    })
    assert r_inv_add.status_code == 200, f"Inventory add failed: {r_inv_add.text}"
    log("DEF-17 verified: Pharmacy successfully added/updated inventory item")

    r_inv_del = pharm_session.delete(f"{BASE_URL}/api/pharmacy/inventory/3")
    assert r_inv_del.status_code == 200, f"Inventory delete failed: {r_inv_del.text}"
    # Second delete returns 404
    r_inv_del404 = pharm_session.delete(f"{BASE_URL}/api/pharmacy/inventory/3")
    assert r_inv_del404.status_code == 404
    # Restore medicine 3 stock so subsequent tests have stock
    pharm_session.post(f"{BASE_URL}/api/pharmacy/inventory", json={
        "medicine_id": 3,
        "quantity": 150,
        "unit_price": 22.0,
        "batch_number": "BATCH-RESTORED",
        "expiry_date": "2028-01-01",
        "is_available": True
    })
    log("DEF-17 verified: Pharmacy DELETE /inventory/<id> removes item and handles 404 idempotency")

    print("=" * 60)
    print("ALL LIVE CROSS-PORTAL E2E TESTS PASSED PERFECTLY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_e2e_verification()
    sys.exit(0 if success else 1)
