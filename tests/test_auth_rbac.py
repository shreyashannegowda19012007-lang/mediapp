"""
Comprehensive unit and integration tests for Authentication & Role-Based Access Control (RBAC).
Verifies registration, credential checking, session persistence, role switching,
Google OAuth flow, boundary isolation, and clinical data privacy.
"""
import pytest
from app.database import get_db, query_db
from app.config import Config

def test_demo_login_flow(client):
    # Customer login
    res = client.post("/api/auth/demo-login", json={"role": "customer"})
    assert res.status_code == 200
    data = res.json
    assert data["status"] == "success"
    assert data["user"]["role"] == "customer"

    # Current user endpoint
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json["authenticated"] is True
    assert me_res.json["user"]["email"] == "demo.customer@mediapp.local"

    # Logout
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    # Me after logout
    after_me = client.get("/api/auth/me")
    assert after_me.json["authenticated"] is False


def test_rbac_unauthorized_access_rejected(client):
    # Unauthenticated access to protected route
    res = client.get("/api/admin/stats")
    assert res.status_code == 401

    # Login as customer
    client.post("/api/auth/demo-login", json={"role": "customer"})

    # Customer attempting to access admin stats
    admin_res = client.get("/api/admin/stats")
    assert admin_res.status_code == 403
    assert "Forbidden" in admin_res.json["error"]

    # Customer attempting to access pharmacy dashboard
    pharm_res = client.get("/api/pharmacy/dashboard")
    assert pharm_res.status_code == 403


def test_customer_registration_success(client):
    payload = {
        "email": "new.patient@example.com",
        "password": "SecurePassword2026!",
        "full_name": "Rohan Verma",
        "phone": "+91 9888877777",
        "address": {
            "address_line1": "104 Sunrise Apartments",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560034"
        }
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json
    assert data["status"] == "success"
    assert data["user"]["email"] == "new.patient@example.com"
    assert data["user"]["role"] == "customer"

    # Verify session is established automatically
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json["authenticated"] is True
    assert me.json["user"]["email"] == "new.patient@example.com"


def test_customer_registration_duplicate_rejected(client):
    payload = {
        "email": "demo.customer@mediapp.local",
        "password": "Password123!",
        "full_name": "Duplicate User",
        "phone": "+91 9999911111"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 409
    assert "already exists" in res.json["error"]


def test_customer_registration_validation(client):
    # Missing email
    res1 = client.post("/api/auth/register", json={"password": "123", "full_name": "A", "phone": "1"})
    assert res1.status_code == 400

    # Short password
    res2 = client.post("/api/auth/register", json={
        "email": "short@example.com",
        "password": "short",
        "full_name": "Short Pwd",
        "phone": "9999999999"
    })
    assert res2.status_code == 400
    assert "at least 8 characters" in res2.json["error"]


def test_credential_login_all_roles(client):
    roles_credentials = [
        ("demo.customer@mediapp.local", "Customer@MediApp2026!", "customer"),
        ("demo.pharmacy@mediapp.local", "Pharmacy@MediApp2026!", "pharmacy"),
        ("demo.delivery@mediapp.local", "Delivery@MediApp2026!", "delivery"),
        ("demo.admin@mediapp.local", "Admin@MediApp2026!", "admin")
    ]

    for email, pwd, expected_role in roles_credentials:
        res = client.post("/api/auth/login", json={"email": email, "password": pwd})
        assert res.status_code == 200, f"Login failed for {email}: {res.json}"
        assert res.json["user"]["role"] == expected_role
        if expected_role == "pharmacy":
            assert res.json["user"]["pharmacy_id"] is not None

        # Verify /api/auth/me reflects this role
        me = client.get("/api/auth/me")
        assert me.json["authenticated"] is True
        assert me.json["user"]["role"] == expected_role

        # Logout before next role
        client.post("/api/auth/logout")


def test_invalid_credentials_rejected(client):
    # Wrong password
    res1 = client.post("/api/auth/login", json={
        "email": "demo.customer@mediapp.local",
        "password": "WrongPassword!"
    })
    assert res1.status_code == 401
    assert "Invalid email or password" in res1.json["error"]

    # Non-existent user
    res2 = client.post("/api/auth/login", json={
        "email": "nonexistent@mediapp.local",
        "password": "AnyPassword123!"
    })
    assert res2.status_code == 401


def test_deactivated_account_login_rejected(app, client):
    # Deactivate demo customer temporarily
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = 0 WHERE email = 'demo.customer@mediapp.local'")
        conn.commit()

    try:
        res = client.post("/api/auth/login", json={
            "email": "demo.customer@mediapp.local",
            "password": "Customer@MediApp2026!"
        })
        assert res.status_code == 403
        assert "deactivated or suspended" in res.json["error"]
    finally:
        with app.app_context():
            conn = get_db()
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_active = 1 WHERE email = 'demo.customer@mediapp.local'")
            conn.commit()


def test_switch_role_authorized_vs_unauthorized(client):
    # Customer attempts to escalate to admin
    client.post("/api/auth/login", json={
        "email": "demo.customer@mediapp.local",
        "password": "Customer@MediApp2026!"
    })
    escalate_res = client.post("/api/auth/switch-role", json={"role": "admin"})
    assert escalate_res.status_code == 403
    assert "not authorized" in escalate_res.json["error"]

    client.post("/api/auth/logout")

    # Admin switches to customer view
    client.post("/api/auth/login", json={
        "email": "demo.admin@mediapp.local",
        "password": "Admin@MediApp2026!"
    })
    switch_res = client.post("/api/auth/switch-role", json={"role": "customer"})
    assert switch_res.status_code == 200
    assert switch_res.json["active_role"] == "customer"


def test_google_oauth_url_and_callback(client):
    # When credentials not configured
    url_res = client.get("/api/auth/google/url")
    assert url_res.status_code in (400, 200)

    # Callback with error parameter
    cb_err = client.get("/api/auth/google/callback?error=access_denied")
    assert cb_err.status_code == 302
    assert "auth_error=access_denied" in cb_err.headers["Location"]

    # Callback with missing parameters
    cb_missing = client.get("/api/auth/google/callback")
    assert cb_missing.status_code == 302
    assert "auth_error=missing_oauth_params" in cb_missing.headers["Location"]


def test_prescription_privacy_delivery_rejected(client):
    """DEF-05: Delivery partner must NOT be permitted to view or download patient prescriptions."""
    # Delivery partner logs in
    client.post("/api/auth/login", json={
        "email": "demo.delivery@mediapp.local",
        "password": "Delivery@MediApp2026!"
    })

    # Attempt to list all prescriptions
    list_res = client.get("/api/prescriptions")
    assert list_res.status_code == 403

    # Attempt to inspect prescription detail
    detail_res = client.get("/api/prescriptions/1")
    assert detail_res.status_code == 403

    # Attempt to download prescription file
    file_res = client.get("/api/prescriptions/1/file")
    assert file_res.status_code == 403


def test_cross_pharmacy_cart_conflict_resolution(client):
    """DEF-15: Cross-pharmacy cart addition must prompt conflict and allow explicit clear."""
    client.post("/api/auth/login", json={
        "email": "demo.customer@mediapp.local",
        "password": "Customer@MediApp2026!"
    })

    # Add item from Pharmacy 1
    add1 = client.post("/api/cart/items", json={"medicine_id": 1, "quantity": 1, "pharmacy_id": 1})
    assert add1.status_code == 200

    # Add item from Pharmacy 2 without clearing
    add2 = client.post("/api/cart/items", json={"medicine_id": 2, "quantity": 1, "pharmacy_id": 2})
    assert add2.status_code == 409
    assert add2.json.get("conflict") is True

    # Add item from Pharmacy 2 with explicit clear_existing=True
    add3 = client.post("/api/cart/items", json={"medicine_id": 2, "quantity": 1, "pharmacy_id": 2, "clear_existing": True})
    assert add3.status_code == 200

    # Verify cart now belongs to Pharmacy 2
    cart = client.get("/api/cart")
    assert cart.status_code == 200
    assert cart.json["pharmacy"]["id"] == 2


def test_static_asset_404_no_html_masking(client):
    """DEF-03: Missing static assets must return 404, not HTML 200 index.html."""
    res = client.get("/static/js/nonexistent_script.js")
    assert res.status_code == 404
    assert "<!DOCTYPE html>" not in res.data.decode("utf-8", errors="ignore")


def test_deactivated_session_revoked_immediately(app):
    """If an active user is deactivated mid-session, any subsequent protected request returns 403."""
    user_client = app.test_client()
    login_res = user_client.post("/api/auth/demo-login", json={"role": "customer"})
    assert login_res.status_code == 200

    # User can access /api/auth/me
    me1 = user_client.get("/api/auth/me")
    assert me1.status_code == 200
    assert me1.json["authenticated"] is True

    # Deactivate in database
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = 0 WHERE email = 'demo.customer@mediapp.local'")
        conn.commit()

    try:
        # Protected route decorated with @login_required returns 403 when user is deactivated in DB
        cart_res = user_client.get("/api/cart")
        assert cart_res.status_code == 403
        assert "deactivated" in cart_res.json["error"]

        # Session was invalidated and cleared upon 403
        me2 = user_client.get("/api/auth/me")
        assert me2.status_code == 200
        assert me2.json["authenticated"] is False
    finally:
        with app.app_context():
            conn = get_db()
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_active = 1 WHERE email = 'demo.customer@mediapp.local'")
            conn.commit()


def test_customer_address_management(client):
    """Customer can list and add saved delivery addresses."""
    client.post("/api/auth/demo-login", json={"role": "customer"})

    # Get initial addresses
    res1 = client.get("/api/auth/addresses")
    assert res1.status_code == 200
    initial_count = len(res1.json["addresses"])

    # Add a new address
    new_addr = {
        "line1": "Flat 801, Prestige Tech Park",
        "line2": "Marathahalli-Sarjapur Outer Ring Road",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560103",
        "is_default": True
    }
    res2 = client.post("/api/auth/addresses", json=new_addr)
    assert res2.status_code == 201
    assert res2.json["address"]["line1"] == "Flat 801, Prestige Tech Park"

    # Verify listed in GET /api/auth/addresses
    res3 = client.get("/api/auth/addresses")
    assert res3.status_code == 200
    assert len(res3.json["addresses"]) == initial_count + 1

    # Verify present in /api/auth/me
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert len(me.json["user"]["addresses"]) == initial_count + 1


def test_suspended_pharmacy_and_delivery_rejected(app):
    """Suspended pharmacy and delivery accounts cannot access portal routes."""
    # Register a new pharmacy user
    pharm_client = app.test_client()
    pharm_client.post("/api/auth/register", json={
        "email": "pending.pharm@example.com",
        "password": "Password123!",
        "full_name": "Pending Pharmacist",
        "phone": "+91 9555566666"
    })

    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = 'pending.pharm@example.com'")
        uid = cur.fetchone()["id"]
        cur.execute("UPDATE users SET role = 'pharmacy' WHERE id = ?", (uid,))
        # Set pharmacy to suspended
        cur.execute("""
            INSERT INTO pharmacies (name, license_number, phone, email, address, city, pincode, rating, status)
            VALUES ('Suspended Meds', 'DL-SUS-001', '+91 9555566666', 'sus@pharm.local', '123 Test St', 'Bengaluru', '560001', 4.0, 'suspended')
        """)
        pharm_id = cur.lastrowid
        cur.execute("""
            INSERT INTO pharmacy_staff (pharmacy_id, user_id, role_title)
            VALUES (?, ?, 'Pharmacist')
        """, (pharm_id, uid))
        conn.commit()

    # Login attempt for suspended pharmacy user is rejected with 403 Forbidden
    login_res = pharm_client.post("/api/auth/login", json={
        "email": "pending.pharm@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 403
    assert "suspended" in login_res.json["error"].lower()

    # Attempt to access pharmacy dashboard is rejected
    dash_res = pharm_client.get("/api/pharmacy/dashboard")
    assert dash_res.status_code in (401, 403)
