"""
Unit and integration tests for Authentication & Role-Based Access Control (RBAC).
Verifies credential checking, session tokens, demo login, and boundary enforcement.
"""
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
