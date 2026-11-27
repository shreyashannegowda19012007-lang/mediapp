"""
Authentication API Routes for MediApp.
Handles email/password login, customer registration, role switching,
demo role authentication, Google OAuth flow, and sessions.
"""
from flask import Blueprint, request, jsonify, session, redirect
from app.services.auth_service import (
    AuthService, set_user_session, clear_user_session, login_required, get_user_from_request
)
from app.config import Config
from app.database import query_db, get_db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Registers a new customer account.
    Restricted to 'customer' role; admin, pharmacy, and delivery roles
    cannot be self-registered via public endpoints.
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address")

    if not email or not password or not full_name or not phone:
        return jsonify({"error": "Full name, email, phone, and password are required."}), 400

    try:
        user = AuthService.register_customer(
            email=email,
            password=password,
            full_name=full_name,
            phone=phone,
            address=address
        )
        set_user_session(user)
        return jsonify({
            "status": "success",
            "message": "Account registered successfully.",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "phone": user["phone"]
            }
        }), 201
    except ValueError as e:
        # Check duplicate
        if "already exists" in str(e).lower():
            return jsonify({"error": str(e)}), 409
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticates user with email and password.
    Returns 401 for invalid credentials and 403 for deactivated/pending/suspended accounts.
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
        
    try:
        user = AuthService.authenticate_credentials(email, password)
        if not user:
            return jsonify({"error": "Invalid email or password."}), 401

        set_user_session(user)
        token = AuthService.create_auth_token(user["id"])
        return jsonify({
            "status": "success",
            "message": "Logged in successfully.",
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "phone": user["phone"],
                "pharmacy_id": session.get("pharmacy_id"),
                "authorized_roles": AuthService.get_authorized_roles(user["id"])
            }
        })
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@auth_bp.route("/switch-role", methods=["POST"])
@login_required
def switch_role():
    """
    Allows an authenticated user to switch their active session role to another
    role they are explicitly authorized to assume (e.g. Admin or Pharmacy acting as Customer).
    """
    data = request.get_json() or {}
    target_role = data.get("role", "").lower().strip()
    user_id = session["user_id"]

    authorized_roles = AuthService.get_authorized_roles(user_id)
    if target_role not in authorized_roles:
        return jsonify({
            "error": f"Forbidden. You are not authorized to assume role '{target_role}'.",
            "authorized_roles": authorized_roles
        }), 403

    user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    if not user:
        clear_user_session()
        return jsonify({"error": "User account not found."}), 404

    session["role"] = target_role
    if target_role == "pharmacy":
        staff = query_db("SELECT pharmacy_id FROM pharmacy_staff WHERE user_id = ?", (user_id,), one=True)
        session["pharmacy_id"] = staff["pharmacy_id"] if staff else None
    else:
        session.pop("pharmacy_id", None)

    return jsonify({
        "status": "success",
        "message": f"Active role switched to '{target_role}'.",
        "active_role": target_role,
        "pharmacy_id": session.get("pharmacy_id")
    })

@auth_bp.route("/demo-login", methods=["POST"])
def demo_login():
    """Allows instant login to demo accounts when APP_MODE is demo."""
    if not Config.is_demo():
        return jsonify({"error": "Demo login is disabled in real production mode."}), 403
        
    data = request.get_json() or {}
    role = data.get("role", "customer").lower()
    
    try:
        user = AuthService.demo_login(role)
        set_user_session(user)
        return jsonify({
            "status": "success",
            "message": f"Authenticated into demo {role} account.",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "phone": user["phone"],
                "pharmacy_id": session.get("pharmacy_id"),
                "authorized_roles": AuthService.get_authorized_roles(user["id"])
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route("/logout", methods=["POST"])
def logout():
    clear_user_session()
    return jsonify({"status": "success", "message": "Logged out successfully."})

@auth_bp.route("/me", methods=["GET"])
@auth_bp.route("/session", methods=["GET"])
def get_current_user():
    user = get_user_from_request()
    if not user:
        return jsonify({
            "status": "success",
            "authenticated": False,
            "user": None,
            "capabilities": Config.get_public_capabilities()
        })
        
    user_id = user["id"]
    user_data = dict(user)
    user_data["user_id"] = user["id"]
    user_data["active_role"] = session.get("role", user["role"])
    user_data["authorized_roles"] = AuthService.get_authorized_roles(user_id)
    user_data["pharmacy_id"] = session.get("pharmacy_id")

    # If pharmacy role, enrich with pharmacy status
    if user["role"] == "pharmacy" or "pharmacy" in user_data["authorized_roles"]:
        staff = query_db("""
            SELECT ps.pharmacy_id, p.name, p.status
            FROM pharmacy_staff ps
            JOIN pharmacies p ON ps.pharmacy_id = p.id
            WHERE ps.user_id = ?
        """, (user_id,), one=True)
        if staff:
            user_data["pharmacy_name"] = staff["name"]
            user_data["pharmacy_status"] = staff["status"]

    # If delivery role, enrich with delivery profile status
    if user["role"] == "delivery" or "delivery" in user_data["authorized_roles"]:
        dp = query_db("SELECT status, is_available FROM delivery_profiles WHERE user_id = ?", (user_id,), one=True)
        if dp:
            user_data["delivery_status"] = dp["status"]
            user_data["delivery_available"] = bool(dp["is_available"])

    # If customer role, enrich with saved addresses
    if user["role"] == "customer" or "customer" in user_data["authorized_roles"]:
        addrs = query_db("SELECT * FROM customer_addresses WHERE user_id = ? ORDER BY is_default DESC, id DESC", (user_id,))
        user_data["addresses"] = [dict(a) for a in addrs]
    
    return jsonify({
        "authenticated": True,
        "user": user_data,
        "capabilities": Config.get_public_capabilities()
    })

@auth_bp.route("/google/url", methods=["GET"])
def google_auth_url():
    try:
        frontend_origin = request.args.get("origin") or request.headers.get("Referer", "")
        role = request.args.get("role", "customer").lower().strip()
        if frontend_origin.startswith("http"):
            import urllib.parse
            parsed = urllib.parse.urlparse(frontend_origin)
            origin = f"{parsed.scheme}://{parsed.netloc}"
        else:
            origin = "http://localhost:3000"
            
        url, state = AuthService.get_google_auth_url(redirect_origin=origin, target_role=role)
        return jsonify({"status": "success", "url": url, "state": state})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route("/google/callback", methods=["GET"])
def google_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    
    # Extract origin safely from state if possible
    frontend_origin = "http://localhost:3000"
    if state:
        try:
            state_data = AuthService.verify_google_state(state)
            frontend_origin = state_data.get("origin", "http://localhost:3000")
        except Exception:
            pass

    if error:
        return redirect(f"{frontend_origin}/?auth_error={error}")
    if not code or not state:
        return redirect(f"{frontend_origin}/?auth_error=missing_oauth_params")
        
    try:
        user, origin, role = AuthService.exchange_google_code(code, state)
        set_user_session(user)
        session["role"] = role
        token = AuthService.create_auth_token(user["id"])
        return redirect(f"{origin}/?login_success=1&role={role}&provider=google&token={token}")
    except Exception as e:
        import urllib.parse
        clean_err = urllib.parse.quote_plus(str(e).replace("\n", " ").replace("\r", " ").strip()[:200])
        return redirect(f"{frontend_origin}/?auth_error={clean_err}")

@auth_bp.route("/google/demo-callback", methods=["GET"])
def google_demo_callback():
    """Simulates immediate Google OAuth sign-in flow for demo mode."""
    state = request.args.get("state")
    frontend_origin = "http://localhost:3000"
    if state:
        try:
            state_data = AuthService.verify_google_state(state)
            frontend_origin = state_data.get("origin", "http://localhost:3000")
        except Exception:
            pass

    if not Config.is_demo():
        return redirect(f"{frontend_origin}/?auth_error=demo_disabled")
    if not state:
        return redirect(f"{frontend_origin}/?auth_error=missing_oauth_params")
    try:
        user, origin, role = AuthService.demo_google_login(state)
        set_user_session(user)
        session["role"] = role
        token = AuthService.create_auth_token(user["id"])
        return redirect(f"{origin}/?login_success=1&role={role}&provider=google&token={token}")
    except Exception as e:
        import urllib.parse
        clean_err = urllib.parse.quote_plus(str(e).replace("\n", " ").replace("\r", " ").strip()[:200])
        return redirect(f"{frontend_origin}/?auth_error={clean_err}")

@auth_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    data = request.get_json() or {}
    full_name = data.get("full_name")
    phone = data.get("phone")
    user_id = session["user_id"]
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users
        SET full_name = COALESCE(?, full_name),
            phone = COALESCE(?, phone),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (full_name, phone, user_id))
    conn.commit()
    
    session["full_name"] = full_name or session["full_name"]
    return jsonify({"status": "success", "message": "Profile updated successfully."})

@auth_bp.route("/addresses", methods=["GET"])
@login_required
def list_addresses():
    user_id = session["user_id"]
    addresses = query_db("""
        SELECT * FROM customer_addresses
        WHERE user_id = ?
        ORDER BY is_default DESC, id DESC
    """, (user_id,))
    res_addrs = []
    for a in addresses:
        ad = dict(a)
        ad["line1"] = ad["address_line1"]
        ad["line2"] = ad.get("address_line2", "")
        res_addrs.append(ad)
    return jsonify({"status": "success", "addresses": res_addrs})

@auth_bp.route("/addresses", methods=["POST"])
@login_required
def add_address():
    data = request.get_json() or {}
    line1 = (data.get("address_line1") or data.get("line1") or "").strip()
    city = data.get("city", "").strip()
    state = (data.get("state") or "Karnataka").strip()
    pincode = (data.get("pincode") or "").strip()
    line2 = (data.get("address_line2") or data.get("line2") or "").strip()
    landmark = (data.get("landmark") or "").strip()
    is_default = 1 if data.get("is_default") else 0
    user_id = session["user_id"]

    if not line1 or not city or not pincode:
        return jsonify({"error": "address_line1 (or line1), city, and pincode are required."}), 400

    conn = get_db()
    cur = conn.cursor()
    if is_default:
        cur.execute("UPDATE customer_addresses SET is_default = 0 WHERE user_id = ?", (user_id,))

    cur.execute("""
        INSERT INTO customer_addresses (
            user_id, address_line1, address_line2, city, state, pincode, landmark, is_default
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, line1, line2, city, state, pincode, landmark, is_default))
    conn.commit()
    new_id = cur.lastrowid
    new_addr = query_db("SELECT * FROM customer_addresses WHERE id = ?", (new_id,), one=True)
    res_addr = dict(new_addr)
    res_addr["line1"] = res_addr["address_line1"]
    res_addr["line2"] = res_addr.get("address_line2", "")
    return jsonify({"status": "success", "message": "Address added successfully.", "address": res_addr}), 201
