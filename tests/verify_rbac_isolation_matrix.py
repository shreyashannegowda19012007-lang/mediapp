"""
Comprehensive Verification of RBAC Isolation Matrix across all 4 Roles:
1. Patient (customer@mediapp.local):
   - Access to /api/pharmacy/orders -> 403 Forbidden
   - Access to /api/delivery/available -> 403 Forbidden
   - Access to /api/admin/stats -> 403 Forbidden
2. Delivery Courier (delivery@mediapp.local):
   - Access to /api/prescriptions -> 403 Forbidden
   - Access to /api/admin/stats -> 403 Forbidden
   - Access to /api/pharmacy/orders -> 403 Forbidden
3. Pharmacist (pharmacy@mediapp.local):
   - Access to /api/admin/stats -> 403 Forbidden
   - Access to /api/delivery/available -> 403 Forbidden
4. Admin (admin@mediapp.local):
   - Authorized access to /api/admin/stats -> 200 OK
   - Authorized access to /api/admin/audit-logs -> 200 OK
   - Authorized access to /api/admin/system-health -> 200 OK
   - Authorized access to /api/admin/pharmacies -> 200 OK
   - Authorized access to /api/admin/users -> 200 OK
"""
import requests

BASE_URL = "http://localhost:5000"

def login_and_get_headers(email, password):
    res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Failed login for {email}: {res.text}"
    data = res.json()
    token = data.get("token")
    return {"Authorization": f"Bearer {token}"}, data.get("user")

def test_rbac_matrix():
    print("=" * 75)
    print("STARTING CROSS-ROLE RBAC ISOLATION MATRIX VERIFICATION")
    print("=" * 75)

    # 1. Authenticate All 4 Roles
    print("\n[Auth] Authenticating all 4 roles...")
    patient_headers, patient_user = login_and_get_headers("customer@mediapp.local", "Customer@123")
    print(f"  -> Patient authenticated: {patient_user['email']} (role: {patient_user['role']}, id: {patient_user['id']})")

    pharmacy_headers, pharmacy_user = login_and_get_headers("pharmacy@mediapp.local", "Pharmacy@123")
    print(f"  -> Pharmacist authenticated: {pharmacy_user['email']} (role: {pharmacy_user['role']}, id: {pharmacy_user['id']})")

    delivery_headers, delivery_user = login_and_get_headers("delivery@mediapp.local", "Delivery@123")
    print(f"  -> Courier authenticated: {delivery_user['email']} (role: {delivery_user['role']}, id: {delivery_user['id']})")

    admin_headers, admin_user = login_and_get_headers("admin@mediapp.local", "Admin@123")
    print(f"  -> Admin authenticated: {admin_user['email']} (role: {admin_user['role']}, id: {admin_user['id']})")

    results = []

    # 2. Patient Rejection Checks
    print("\n[Patient RBAC Rejection Checks]")
    # Patient -> Staff Pharmacy Orders
    res = requests.get(f"{BASE_URL}/api/pharmacy/orders", headers=patient_headers)
    print(f"  Patient -> GET /api/pharmacy/orders : HTTP {res.status_code} (Expected 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"
    results.append(("Patient", "GET /api/pharmacy/orders", res.status_code, 403, "PASS"))

    # Patient -> Delivery Available Runs
    res = requests.get(f"{BASE_URL}/api/delivery/available", headers=patient_headers)
    print(f"  Patient -> GET /api/delivery/available : HTTP {res.status_code} (Expected 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"
    results.append(("Patient", "GET /api/delivery/available", res.status_code, 403, "PASS"))

    # Patient -> Admin Stats
    res = requests.get(f"{BASE_URL}/api/admin/stats", headers=patient_headers)
    print(f"  Patient -> GET /api/admin/stats : HTTP {res.status_code} (Expected 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"
    results.append(("Patient", "GET /api/admin/stats", res.status_code, 403, "PASS"))

    # 3. Courier Rejection Checks
    print("\n[Courier RBAC Rejection Checks]")
    # Courier -> Patient Prescriptions
    res = requests.get(f"{BASE_URL}/api/prescriptions", headers=delivery_headers)
    print(f"  Courier -> GET /api/prescriptions : HTTP {res.status_code} (Expected 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"
    results.append(("Courier", "GET /api/prescriptions", res.status_code, 403, "PASS"))

    # Courier -> Admin Stats
    res = requests.get(f"{BASE_URL}/api/admin/stats", headers=delivery_headers)
    print(f"  Courier -> GET /api/admin/stats : HTTP {res.status_code} (Expected 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"
    results.append(("Courier", "GET /api/admin/stats", res.status_code, 403, "PASS"))

    # Courier -> Pharmacy Orders
    res = requests.get(f"{BASE_URL}/api/pharmacy/orders", headers=delivery_headers)
    print(f"  Courier -> GET /api/pharmacy/orders : HTTP {res.status_code} (Expected 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"
    results.append(("Courier", "GET /api/pharmacy/orders", res.status_code, 403, "PASS"))

    # 4. Pharmacist Rejection Checks
    print("\n[Pharmacist RBAC Rejection Checks]")
    # Pharmacist -> Admin Stats
    res = requests.get(f"{BASE_URL}/api/admin/stats", headers=pharmacy_headers)
    print(f"  Pharmacist -> GET /api/admin/stats : HTTP {res.status_code} (Expected 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"
    results.append(("Pharmacist", "GET /api/admin/stats", res.status_code, 403, "PASS"))

    # Pharmacist -> Delivery Available Runs
    res = requests.get(f"{BASE_URL}/api/delivery/available", headers=pharmacy_headers)
    print(f"  Pharmacist -> GET /api/delivery/available : HTTP {res.status_code} (Expected 403)")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"
    results.append(("Pharmacist", "GET /api/delivery/available", res.status_code, 403, "PASS"))

    # 5. Admin Authorization Checks
    print("\n[Admin Authorized Access Checks]")
    # Admin -> Admin Stats
    res = requests.get(f"{BASE_URL}/api/admin/stats", headers=admin_headers)
    print(f"  Admin -> GET /api/admin/stats : HTTP {res.status_code} (Expected 200)")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    results.append(("Admin", "GET /api/admin/stats", res.status_code, 200, "PASS"))

    # Admin -> Audit Logs
    res = requests.get(f"{BASE_URL}/api/admin/audit-logs", headers=admin_headers)
    print(f"  Admin -> GET /api/admin/audit-logs : HTTP {res.status_code} (Expected 200)")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    results.append(("Admin", "GET /api/admin/audit-logs", res.status_code, 200, "PASS"))

    # Admin -> System Health
    res = requests.get(f"{BASE_URL}/api/admin/system-health", headers=admin_headers)
    print(f"  Admin -> GET /api/admin/system-health : HTTP {res.status_code} (Expected 200)")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    results.append(("Admin", "GET /api/admin/system-health", res.status_code, 200, "PASS"))

    # Admin -> Pharmacies
    res = requests.get(f"{BASE_URL}/api/admin/pharmacies", headers=admin_headers)
    print(f"  Admin -> GET /api/admin/pharmacies : HTTP {res.status_code} (Expected 200)")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    results.append(("Admin", "GET /api/admin/pharmacies", res.status_code, 200, "PASS"))

    # Admin -> Users
    res = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers)
    print(f"  Admin -> GET /api/admin/users : HTTP {res.status_code} (Expected 200)")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    results.append(("Admin", "GET /api/admin/users", res.status_code, 200, "PASS"))

    print("\n" + "=" * 75)
    print("RBAC ISOLATION MATRIX SUMMARY:")
    print(f"{'Role':<12} | {'Endpoint Attempted':<32} | {'Status':<6} | {'Expected':<8} | {'Result':<6}")
    print("-" * 75)
    for role, ep, status, expected, res_str in results:
        print(f"{role:<12} | {ep:<32} | {status:<6} | {expected:<8} | {res_str:<6}")
    print("=" * 75)
    print("ALL 13 RBAC ISOLATION CHECKS PASSED PERFECTLY (100% ENFORCEMENT)!")

if __name__ == "__main__":
    test_rbac_matrix()
