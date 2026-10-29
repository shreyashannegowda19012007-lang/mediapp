"""
Authentication API Routes for MediApp.
Handles email/password login, demo role authentication, Google OAuth flow, and sessions.
"""
from flask import Blueprint, request, jsonify, session, redirect
from app.services.auth_service import (
    AuthService, set_user_session, clear_user_session, login_required
)
from app.config import Config
from app.database import query_db, get_db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
        
    user = AuthService.authenticate_credentials(email, password)
    if not user:
        return jsonify({"error": "Invalid email or password."}), 401
        
    set_user_session(user)
    return jsonify({
        "status": "success",
        "message": "Logged in successfully.",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "phone": user["phone"]
        }
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
                "pharmacy_id": session.get("pharmacy_id")
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route("/logout", methods=["POST"])
def logout():
    clear_user_session()
    return jsonify({"status": "success", "message": "Logged out successfully."})

@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "authenticated": False,
            "user": None,
            "capabilities": Config.get_public_capabilities()
        })
        
    user = query_db("SELECT id, email, full_name, phone, role, profile_image FROM users WHERE id = ?", (user_id,), one=True)
    if not user:
        clear_user_session()
        return jsonify({"authenticated": False, "user": None, "capabilities": Config.get_public_capabilities()})
        
    user_data = dict(user)
    user_data["pharmacy_id"] = session.get("pharmacy_id")
    
    return jsonify({
        "authenticated": True,
        "user": user_data,
        "capabilities": Config.get_public_capabilities()
    })

@auth_bp.route("/google/url", methods=["GET"])
def google_auth_url():
    try:
        url, state = AuthService.get_google_auth_url()
        return jsonify({"status": "success", "url": url, "state": state})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route("/google/callback", methods=["GET"])
def google_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    
    if error:
        return redirect(f"/?auth_error={error}")
    if not code or not state:
        return redirect("/?auth_error=missing_oauth_params")
        
    try:
        user = AuthService.exchange_google_code(code, state)
        set_user_session(user)
        return redirect("/?login_success=1")
    except Exception as e:
        return redirect(f"/?auth_error={str(e)}")

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
