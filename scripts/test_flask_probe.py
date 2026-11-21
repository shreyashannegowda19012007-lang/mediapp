"""
Forensic test probe using Flask test_client directly.
Audits all route boundary conditions, security checks, and data validation rules.
"""
from app import create_app
import json

app = create_app()

def audit():
    client = app.test_client()
    findings = []

    print("=" * 60)
    print("STARTING TEST_CLIENT FORENSIC AUDIT")
    print("=" * 60)

    # 1. Login as customer
    r_login = client.post("/api/auth/login", json={"email": "customer@mediapp.local", "password": "Customer@123", "role": "customer"})
    print(f"Customer login: {r_login.status_code}")

    # PROBE 1: Negative quantity in cart
    r = client.post("/api/cart/items", json={"medicine_id": 1, "quantity": -5})
    print(f"Negative quantity (-5): {r.status_code} - {r.get_json()}")
    if r.status_code == 200:
        findings.append({
            "code": "DEF-AUDIT-01",
            "title": "Cart accepts negative quantities allowing negative total calculation",
            "severity": "Critical",
            "layer": "Backend / Cart API",
            "file": "app/routes/cart_routes.py",
            "details": f"Posting quantity=-5 returned HTTP 200: {r.get_json()}"
        })

    # PROBE 2: Zero quantity in cart
    r = client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 0})
    print(f"Zero quantity (0): {r.status_code} - {r.get_json()}")
    if r.status_code == 200:
        findings.append({
            "code": "DEF-AUDIT-02",
            "title": "Cart accepts zero quantity item without validation",
            "severity": "Medium",
            "layer": "Backend / Cart API",
            "file": "app/routes/cart_routes.py",
            "details": f"Posting quantity=0 returned HTTP 200: {r.get_json()}"
        })

    # PROBE 3: Non-existent medicine ID in cart
    r = client.post("/api/cart/items", json={"medicine_id": 999999, "quantity": 1})
    print(f"Non-existent medicine (999999): {r.status_code} - {r.get_json()}")
    if r.status_code == 200:
        findings.append({
            "code": "DEF-AUDIT-03",
            "title": "Cart permits adding non-existent medicine IDs to active cart",
            "severity": "High",
            "layer": "Backend / Cart API",
            "file": "app/routes/cart_routes.py",
            "details": f"Posting non-existent medicine_id=999999 returned HTTP 200: {r.get_json()}"
        })

    # PROBE 4: Extremely large quantity exceeding inventory
    r = client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 500000})
    print(f"Excessive quantity (500000): {r.status_code} - {r.get_json()}")
    if r.status_code == 200:
        findings.append({
            "code": "DEF-AUDIT-04",
            "title": "Cart permits adding quantities far exceeding warehouse stock",
            "severity": "High",
            "layer": "Backend / Cart API",
            "file": "app/routes/cart_routes.py",
            "details": f"Posting quantity=500000 returned HTTP 200 without inventory limit check"
        })

    # Clear cart
    client.delete("/api/cart")

    # PROBE 5: Order with empty cart
    r = client.post("/api/orders", json={"delivery_address": "Flat 101, Test Rd"})
    print(f"Order with empty cart: {r.status_code} - {r.get_json()}")
    if r.status_code in [200, 201]:
        findings.append({
            "code": "DEF-AUDIT-05",
            "title": "Order creation allowed with zero items in cart",
            "severity": "High",
            "layer": "Backend / Order API",
            "file": "app/routes/order_routes.py",
            "details": f"Creating order on empty cart succeeded with HTTP {r.status_code}: {r.get_json()}"
        })

    # PROBE 6: Order with whitespace / blank address
    client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
    r = client.post("/api/orders", json={"delivery_address": "   \n\t  "})
    print(f"Order with blank address: {r.status_code} - {r.get_json()}")
    if r.status_code in [200, 201]:
        findings.append({
            "code": "DEF-AUDIT-06",
            "title": "Order creation permitted with whitespace-only delivery address",
            "severity": "Medium",
            "layer": "Backend / Order API",
            "file": "app/routes/order_routes.py",
            "details": f"Order created with blank address: {r.get_json()}"
        })

    client.delete("/api/cart")

    # PROBE 7: Rx-required drug ordered without prescription_id
    r_med = client.get("/api/medicines?rx=1&limit=1")
    rx_meds = r_med.get_json().get("medicines", [])
    if rx_meds:
        med_id = rx_meds[0]["id"]
        client.post("/api/cart/items", json={"medicine_id": med_id, "quantity": 1})
        r_order_no_rx = client.post("/api/orders", json={"delivery_address": "Valid Address", "prescription_id": None})
        print(f"Order Rx medicine without prescription: {r_order_no_rx.status_code} - {r_order_no_rx.get_json()}")
        if r_order_no_rx.status_code in [200, 201]:
            findings.append({
                "code": "DEF-AUDIT-07",
                "title": "Prescription-only formulation ordered without attaching approved doctor prescription",
                "severity": "Critical",
                "layer": "Clinical Safety / Order API",
                "file": "app/routes/order_routes.py",
                "details": f"Order created for Rx drug #{med_id} without prescription: {r_order_no_rx.get_json()}"
            })
        client.delete("/api/cart")

    # PROBE 8: Order with arbitrary fake prescription_id (e.g. 999999 or belonging to someone else)
    client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
    r_fake_rx = client.post("/api/orders", json={"delivery_address": "Valid Address", "prescription_id": 999999})
    print(f"Order with non-existent prescription_id=999999: {r_fake_rx.status_code} - {r_fake_rx.get_json()}")
    if r_fake_rx.status_code in [200, 201]:
        findings.append({
            "code": "DEF-AUDIT-08",
            "title": "Order links non-existent or unverified prescription_id without foreign key or owner check",
            "severity": "High",
            "layer": "Clinical Safety / Order API",
            "file": "app/routes/order_routes.py",
            "details": f"Order created linking non-existent prescription_id=999999: {r_fake_rx.get_json()}"
        })
    client.delete("/api/cart")

    # PROBE 9: Cross-customer IDOR on Order
    # Create customer 2
    client2 = app.test_client()
    client2.post("/api/auth/register", json={"email": "cust2@test.local", "password": "Password123!", "full_name": "Cust Two", "phone": "9999999999"})
    client2.post("/api/auth/login", json={"email": "cust2@test.local", "password": "Password123!"})

    # Cust 1 creates an order
    client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1})
    res_ord = client.post("/api/orders", json={"delivery_address": "Customer 1 Private Home"})
    ord_id = res_ord.get_json().get("order_id")
    print(f"Customer 1 created order #{ord_id}")

    # Cust 2 tries to fetch Cust 1 order
    r_idor_ord = client2.get(f"/api/orders/{ord_id}")
    print(f"Customer 2 fetching Customer 1's order #{ord_id}: {r_idor_ord.status_code} - {r_idor_ord.get_json()}")
    if r_idor_ord.status_code == 200:
        findings.append({
            "code": "DEF-AUDIT-09",
            "title": "IDOR: Customer 2 can inspect Customer 1's private order details and home address",
            "severity": "High",
            "layer": "Security / Order API",
            "file": "app/routes/order_routes.py",
            "details": f"Customer 2 accessed Customer 1's order details: {r_idor_ord.get_json()}"
        })

    # PROBE 10: Customer 2 tries to cancel Customer 1's order
    r_cancel_idor = client2.post(f"/api/orders/{ord_id}/cancel")
    print(f"Customer 2 cancelling Customer 1's order #{ord_id}: {r_cancel_idor.status_code}")
    if r_cancel_idor.status_code == 200:
        findings.append({
            "code": "DEF-AUDIT-10",
            "title": "IDOR: Customer 2 can cancel Customer 1's order",
            "severity": "Critical",
            "layer": "Security / Order API",
            "file": "app/routes/order_routes.py",
            "details": f"Customer 2 cancelled Customer 1's order without ownership check"
        })

    # PROBE 11: Catalogue limit=0 or limit=-1 or limit=1000000
    r_lim_huge = client.get("/api/medicines?limit=1000000")
    meds_count = len(r_lim_huge.get_json().get("medicines", []))
    print(f"Limit 1,000,000 count: {meds_count}")
    if meds_count > 500:
        findings.append({
            "code": "DEF-AUDIT-11",
            "title": "Catalogue endpoint uncapped pagination limit (DoS amplification risk)",
            "severity": "Medium",
            "layer": "Backend / Medicines API",
            "file": "app/routes/medicine_routes.py",
            "details": f"GET /api/medicines?limit=1000000 returns all {meds_count} items without max limit cap."
        })

    # PROBE 12: Delivery Driver accessing customer full name / prescriptions
    client_driver = app.test_client()
    client_driver.post("/api/auth/login", json={"email": "delivery@mediapp.local", "password": "Delivery@123", "role": "delivery"})
    r_driver_rx = client_driver.get("/api/prescriptions")
    print(f"Delivery driver access to /api/prescriptions: {r_driver_rx.status_code}")
    if r_driver_rx.status_code == 200:
        findings.append({
            "code": "DEF-AUDIT-12",
            "title": "Delivery drivers permitted access to customer medical prescriptions queue",
            "severity": "Critical",
            "layer": "Security / Privacy / RBAC",
            "file": "app/routes/prescription_routes.py",
            "details": "Delivery drivers can inspect customer medical prescriptions list."
        })

    print("\n" + "=" * 60)
    print(f"AUDIT PROBE RESULTS: {len(findings)} CONFIRMED DEFECTS")
    print("=" * 60)
    for f in findings:
        print(f"[{f['severity']}] {f['code']}: {f['title']}")

    with open("scratch_audit_results.json", "w") as fp:
        json.dump(findings, fp, indent=2)

if __name__ == "__main__":
    audit()
