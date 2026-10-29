"""
Authentication and Role-Based Access Control (RBAC) Service for MediApp.
Handles password hashing, session state, Google OAuth 2.0 exchange, and authorization decorators.
"""
from functools import wraps
from flask import session, jsonify, request, g, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import secrets
from app.config import Config
from app.database import get_db, query_db

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return generate_password_hash(password)

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        if not hashed:
            return False
        return check_password_hash(hashed, password)

    @classmethod
    def authenticate_credentials(cls, email: str, password: str) -> dict | None:
        """Authenticates user with email and password."""
        user = query_db(
            "SELECT * FROM users WHERE email = ? AND is_active = 1",
            (email.strip().lower(),),
            one=True
        )
        if not user or not user["password_hash"]:
            return None
        if not cls.verify_password(password, user["password_hash"]):
            return None
        return dict(user)

    @classmethod
    def demo_login(cls, role: str) -> dict | None:
        """Performs quick authentication into verified demo role account."""
        if not Config.is_demo():
            raise PermissionError("Demo login is disabled in real production mode.")
            
        role_map = {
            "customer": "demo.customer@mediapp.local",
            "pharmacy": "demo.pharmacy@mediapp.local",
            "delivery": "demo.delivery@mediapp.local",
            "admin": "demo.admin@mediapp.local"
        }
        target_email = role_map.get(role)
        if not target_email:
            raise ValueError(f"Invalid demo role '{role}'.")
            
        user = query_db("SELECT * FROM users WHERE email = ? AND is_active = 1", (target_email,), one=True)
        if not user:
            raise ValueError(f"Demo user for role '{role}' not found. Please run seed script.")
        return dict(user)

    @classmethod
    def get_google_auth_url(cls) -> tuple[str, str]:
        """Generates Google OAuth 2.0 authorization URL with anti-CSRF state token."""
        if not (Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET):
            raise ValueError("Google OAuth credentials are not configured on the server.")
            
        state = secrets.token_urlsafe(24)
        session["oauth_state"] = state
        
        params = {
            "client_id": Config.GOOGLE_CLIENT_ID,
            "redirect_uri": Config.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account"
        }
        encoded_params = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{encoded_params}"
        return auth_url, state

    @classmethod
    def exchange_google_code(cls, code: str, state: str) -> dict:
        """Exchanges authorization code for user info and synchronizes local account."""
        stored_state = session.get("oauth_state")
        if not stored_state or not hmac_compare_safe(stored_state, state):
            raise ValueError("Invalid or expired OAuth state parameter (potential CSRF).")

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": Config.GOOGLE_CLIENT_ID,
            "client_secret": Config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": Config.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        token_res = requests.post(token_url, data=data, timeout=10.0)
        if token_res.status_code != 200:
            raise ValueError(f"Google token exchange failed: {token_res.text}")
            
        tokens = token_res.json()
        access_token = tokens.get("access_token")
        
        # Fetch user profile
        userinfo_res = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0
        )
        if userinfo_res.status_code != 200:
            raise ValueError("Failed to fetch Google user profile.")
            
        google_user = userinfo_res.json()
        google_id = google_user.get("sub")
        email = google_user.get("email", "").lower().strip()
        name = google_user.get("name") or email.split("@")[0]
        picture = google_user.get("picture")

        conn = get_db()
        cur = conn.cursor()
        
        # Check if user already exists
        existing = query_db("SELECT * FROM users WHERE google_id = ? OR email = ?", (google_id, email), one=True)
        if existing:
            cur.execute("""
                UPDATE users SET google_id = ?, profile_image = COALESCE(?, profile_image), updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (google_id, picture, existing["id"]))
            conn.commit()
            return query_db("SELECT * FROM users WHERE id = ?", (existing["id"],), one=True)
        else:
            # New user registers via Google OAuth as 'customer'
            cur.execute("""
                INSERT INTO users (email, full_name, role, google_id, profile_image, is_active)
                VALUES (?, ?, 'customer', ?, ?, 1)
            """, (email, name, google_id, picture))
            new_id = cur.lastrowid
            conn.commit()
            return query_db("SELECT * FROM users WHERE id = ?", (new_id,), one=True)


def hmac_compare_safe(val1: str, val2: str) -> bool:
    import hmac
    return hmac.compare_digest(str(val1), str(val2))


def set_user_session(user: Mapping[str, Any]):
    """Stores minimal authoritative user information in secure server session."""
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["email"] = user["email"]
    session["full_name"] = user["full_name"]
    
    # If pharmacy user, store associated pharmacy_id
    if user["role"] == "pharmacy":
        staff_row = query_db("SELECT pharmacy_id FROM pharmacy_staff WHERE user_id = ?", (user["id"],), one=True)
        session["pharmacy_id"] = staff_row["pharmacy_id"] if staff_row else None
    else:
        session.pop("pharmacy_id", None)


def clear_user_session():
    """Wipes session on logout."""
    session.clear()


def login_required(f):
    """Decorator requiring active session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required. Please sign in."}), 401
        return f(*args, **kwargs)
    return decorated_function


def roles_required(*allowed_roles):
    """Decorator strictly enforcing permitted user roles on backend."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Authentication required."}), 401
            user_role = session.get("role")
            if user_role not in allowed_roles:
                return jsonify({
                    "error": f"Forbidden. Role '{user_role}' does not have access to this resource.",
                    "required_roles": list(allowed_roles)
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
