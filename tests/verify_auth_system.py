"""
Comprehensive Verification Script for MediApp Authentication & Google OAuth Simulation.
Validates:
1. Google OAuth URL generation in Demo Mode
2. Google OAuth callback and session creation ("Shreyash (Google Verified)")
3. Profile retrieval and address association
4. Standard credential sign-in across all 4 roles (Customer, Pharmacy, Delivery, Admin)
5. Fallback demo password support
6. Cross-origin / localhost resolution
"""
import requests

def test_auth_system():
    base = "http://127.0.0.1:5000"
    s = requests.Session()

    # 1. Unauthenticated capabilities check
    r = s.get(f"{base}/api/auth/me")
    assert r.status_code == 200, f"Failed /api/auth/me: {r.text}"
    caps = r.json().get("capabilities", {})
    print(f"[OK] Capabilities: google_oauth_mode={caps.get('google_oauth_mode')}, configured={caps.get('google_oauth_configured')}")
    assert caps.get("google_oauth_configured") is True

    # 2. Google OAuth URL generation
    r = s.get(f"{base}/api/auth/google/url")
    assert r.status_code == 200, f"Failed /api/auth/google/url: {r.text}"
    auth_data = r.json()
    auth_url = auth_data["url"]
    print(f"[OK] Google Auth URL returned: {auth_url}")
    assert "demo-callback" in auth_url

    # 3. Simulate Google OAuth callback
    r = s.get(f"{base}{auth_url}", allow_redirects=False)
    assert r.status_code == 302, f"Failed callback redirect: {r.status_code}"
    loc = r.headers.get("Location")
    print(f"[OK] Callback redirected to: {loc}")
    assert "login_success=1" in loc
    assert "provider=google" in loc

    # 4. Profile retrieval as Google user
    r = s.get(f"{base}/api/auth/me")
    assert r.status_code == 200
    user = r.json()["user"]
    print(f"[OK] Authenticated Google User: {user['full_name']} <{user['email']}> Role: {user['role']}")
    assert user["full_name"] == "Shreyash (Google Verified)"
    assert user["role"] == "customer"
    assert len(user["addresses"]) >= 1

    # 5. Logout
    r = s.post(f"{base}/api/auth/logout")
    assert r.status_code == 200
    print("[OK] Logout successful")

    # 6. Test all 4 standard credential logins
    test_creds = [
        ("customer@mediapp.local", "Customer@123", "customer"),
        ("pharmacy@mediapp.local", "Pharmacy@123", "pharmacy"),
        ("delivery@mediapp.local", "Delivery@123", "delivery"),
        ("admin@mediapp.local", "Admin@123", "admin"),
        ("customer@mediapp.local", "Password@123", "customer"),  # test demo fallback
        ("pharmacy@mediapp.local", "Password@123", "pharmacy"),  # test demo fallback
    ]
    for email, pwd, expected_role in test_creds:
        s2 = requests.Session()
        r = s2.post(f"{base}/api/auth/login", json={"email": email, "password": pwd})
        assert r.status_code == 200, f"Failed {email} with pwd {pwd}: {r.text}"
        data = r.json()
        assert data["user"]["role"] == expected_role
        print(f"[OK] Credential Login: {email} (pwd={pwd}) -> Role: {data['user']['role']} ({data['user']['full_name']})")

    # 7. Test 1-click Demo logins across all 4 roles
    for role in ["customer", "pharmacy", "delivery", "admin"]:
        s3 = requests.Session()
        r = s3.post(f"{base}/api/auth/demo-login", json={"role": role})
        assert r.status_code == 200, f"Failed demo login {role}: {r.text}"
        data = r.json()
        assert data["user"]["role"] == role
        print(f"[OK] Demo 1-Click Login: {role} -> {data['user']['full_name']}")

    # 8. Test localhost:5000 resolution
    r_local = requests.get("http://localhost:5000/api/auth/me")
    assert r_local.status_code == 200
    print("[OK] http://localhost:5000 responded 200 OK")

    print("\nALL AUTHENTICATION & GOOGLE OAUTH TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_auth_system()
