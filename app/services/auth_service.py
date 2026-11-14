"""
Authentication and Role-Based Access Control (RBAC) Service for MediApp.
Handles password hashing, customer registration, session state, Google OAuth 2.0 exchange,
and authorization decorators.
"""
from functools import wraps
from typing import Mapping, Any, Optional, List, Tuple
from flask import session, jsonify, request, g, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import secrets
import re
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
    def register_customer(
        cls,
        email: str,
        password: str,
        full_name: str,
        phone: str,
        address: Optional[dict] = None
    ) -> dict:
        """
        Registers a new customer account with strict credential validation
        and duplicate detection. Administrators and staff cannot be registered here.
        """
        clean_email = email.strip().lower()
        if not clean_email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_email):
            raise ValueError("A valid email address is required.")

        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        clean_name = full_name.strip()
        if not clean_name:
            raise ValueError("Full name is required.")

        clean_phone = phone.strip()
        if not clean_phone:
            raise ValueError("Phone number is required.")

        # Duplicate email check
        existing = query_db("SELECT id FROM users WHERE email = ?", (clean_email,), one=True)
        if existing:
            raise ValueError("An account with this email address already exists. Please sign in.")

        conn = get_db()
        cur = conn.cursor()
        password_hash = cls.hash_password(password)

        cur.execute("""
            INSERT INTO users (email, password_hash, full_name, phone, role, is_active)
            VALUES (?, ?, ?, ?, 'customer', 1)
        """, (clean_email, password_hash, clean_name, clean_phone))
        new_user_id = cur.lastrowid

        # Optional initial delivery address
        if address and isinstance(address, dict):
            line1 = address.get("address_line1", "").strip()
            city = address.get("city", "").strip()
            state = address.get("state", "").strip()
            pincode = address.get("pincode", "").strip()
            if line1 and city and pincode:
                cur.execute("""
                    INSERT INTO customer_addresses (
                        user_id, address_line1, address_line2, city, state, pincode, landmark, is_default
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    new_user_id, line1, address.get("address_line2", ""),
                    city, state or "Karnataka", pincode, address.get("landmark", "")
                ))

        conn.commit()
        return dict(query_db("SELECT * FROM users WHERE id = ?", (new_user_id,), one=True))

    @classmethod
    def authenticate_credentials(cls, email: str, password: str) -> dict | None:
        """
        Authenticates user with email and password.
        Validates account activation and role-specific approval status.
        """
        clean_email = email.strip().lower()
        user = query_db("SELECT * FROM users WHERE email = ?", (clean_email,), one=True)
        if not user or not user["password_hash"]:
            return None

        if not cls.verify_password(password, user["password_hash"]):
            # In demo mode, also allow standard role passwords or Password@123 as fallback for local accounts
            is_valid_demo_fallback = (
                Config.is_demo() and 
                (user["email"].endswith("@mediapp.local") or user["email"].startswith("demo.")) and
                password in [
                    f"{user['role'].capitalize()}@123",
                    "Password@123",
                    "Customer@123",
                    "Pharmacy@123",
                    "Delivery@123",
                    "Admin@123",
                    "Demo@Customer123",
                    "Demo@Pharmacy123",
                    "Demo@Delivery123",
                    "Demo@Admin123",
                    "Customer@MediApp2026!",
                    "Pharmacy@MediApp2026!",
                    "Delivery@MediApp2026!",
                    "Admin@MediApp2026!"
                ]
            )
            if not is_valid_demo_fallback:
                return None

        if not user["is_active"]:
            raise PermissionError("Your account has been deactivated or suspended. Please contact support.")

        # Role-specific verification checks
        if user["role"] == "pharmacy":
            staff = query_db("SELECT pharmacy_id FROM pharmacy_staff WHERE user_id = ?", (user["id"],), one=True)
            if not staff:
                raise PermissionError("Your pharmacy account is not associated with any licensed store.")
            pharm = query_db("SELECT status, name FROM pharmacies WHERE id = ?", (staff["pharmacy_id"],), one=True)
            if not pharm:
                raise PermissionError("Associated pharmacy store not found.")
            if pharm["status"] == "pending":
                raise PermissionError("Your pharmacy account is pending administrative approval.")
            if pharm["status"] in ("suspended", "rejected"):
                raise PermissionError(f"Pharmacy account '{pharm['name']}' has been suspended or rejected.")

        elif user["role"] == "delivery":
            dp = query_db("SELECT status FROM delivery_profiles WHERE user_id = ?", (user["id"],), one=True)
            if not dp:
                raise PermissionError("Your delivery partner account has no registered delivery profile.")
            if dp["status"] == "pending":
                raise PermissionError("Your delivery partner account is pending administrative approval.")
            if dp["status"] in ("suspended", "rejected"):
                raise PermissionError(f"Your delivery partner account has been {dp['status']}.")

        return dict(user)

    @classmethod
    def get_authorized_roles(cls, user_id: int) -> List[str]:
        """Returns verified roles that the specified user identity is authorized to assume."""
        user = query_db("SELECT role, is_active FROM users WHERE id = ?", (user_id,), one=True)
        if not user or not user["is_active"]:
            return []

        primary_role = user["role"]
        roles = []

        if primary_role == "admin":
            roles = ["admin", "customer"]
        elif primary_role == "pharmacy":
            staff = query_db("SELECT pharmacy_id FROM pharmacy_staff WHERE user_id = ?", (user_id,), one=True)
            if staff:
                pharm = query_db("SELECT status FROM pharmacies WHERE id = ?", (staff["pharmacy_id"],), one=True)
                if pharm and pharm["status"] == "approved":
                    roles.append("pharmacy")
            roles.append("customer")
        elif primary_role == "delivery":
            dp = query_db("SELECT status FROM delivery_profiles WHERE user_id = ?", (user_id,), one=True)
            if dp and dp["status"] == "approved":
                roles.append("delivery")
            roles.append("customer")
        else:
            roles.append("customer")

        return list(dict.fromkeys(roles))

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
        """Generates Google OAuth 2.0 authorization URL with anti-CSRF state token and nonce."""
        state = secrets.token_urlsafe(24)
        session["oauth_state"] = state

        if not (Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET):
            if Config.is_demo():
                return f"/api/auth/google/demo-callback?state={state}", state
            raise ValueError("Google OAuth credentials are not configured on the server. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.")
            
        nonce = secrets.token_urlsafe(16)
        session["oauth_nonce"] = nonce
        
        params = {
            "client_id": Config.GOOGLE_CLIENT_ID,
            "redirect_uri": Config.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "access_type": "online",
            "prompt": "select_account"
        }
        encoded_params = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{encoded_params}"
        return auth_url, state

    @classmethod
    def demo_google_login(cls, state: str) -> dict:
        """Completes simulated Google OAuth sign-in for demo mode."""
        stored_state = session.get("oauth_state")
        if not stored_state or not hmac_compare_safe(stored_state, state):
            raise ValueError("Invalid or expired OAuth state parameter (potential CSRF).")

        google_email = "google.customer@mediapp.local"
        google_name = "Shreyash (Google Verified)"
        google_id = "google_demo_1082736451928374"
        
        conn = get_db()
        cur = conn.cursor()
        existing = query_db("SELECT * FROM users WHERE google_id = ? OR email = ?", (google_id, google_email), one=True)
        if existing:
            cur.execute("""
                UPDATE users
                SET google_id = ?, full_name = COALESCE(full_name, ?), is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (google_id, google_name, existing["id"]))
            conn.commit()
            return dict(query_db("SELECT * FROM users WHERE id = ?", (existing["id"],), one=True))
        else:
            cur.execute("""
                INSERT INTO users (email, full_name, role, google_id, is_active, created_at, updated_at)
                VALUES (?, ?, 'customer', ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (google_email, google_name, google_id))
            conn.commit()
            new_id = cur.lastrowid
            
            # Seed default delivery address for demo google user
            cur.execute("""
                INSERT INTO customer_addresses (
                    user_id, address_line1, address_line2, city, state, pincode, landmark, is_default
                ) VALUES (?, 'Google Campus / 100 Feet Rd', 'Indiranagar', 'Bengaluru', 'Karnataka', '560038', 'Metro Pillar 42', 1)
            """, (new_id,))
            conn.commit()
            return dict(query_db("SELECT * FROM users WHERE id = ?", (new_id,), one=True))

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
        email_verified = google_user.get("email_verified", True)
        if not email_verified:
            raise ValueError("Google account email address is not verified by Google.")

        name = google_user.get("name") or email.split("@")[0]
        picture = google_user.get("picture")

        conn = get_db()
        cur = conn.cursor()
        
        # Check if user already exists
        existing = query_db("SELECT * FROM users WHERE google_id = ? OR email = ?", (google_id, email), one=True)
        if existing:
            if not existing["is_active"]:
                raise PermissionError("Your account has been deactivated or suspended.")

            if existing["role"] == "pharmacy":
                staff = query_db("SELECT pharmacy_id FROM pharmacy_staff WHERE user_id = ?", (existing["id"],), one=True)
                if not staff:
                    raise PermissionError("Your pharmacy account is not associated with any licensed store.")
                pharm = query_db("SELECT status FROM pharmacies WHERE id = ?", (staff["pharmacy_id"],), one=True)
                if not pharm or pharm["status"] != "approved":
                    raise PermissionError("Your associated pharmacy account is not approved or is suspended.")

            elif existing["role"] == "delivery":
                dp = query_db("SELECT status FROM delivery_profiles WHERE user_id = ?", (existing["id"],), one=True)
                if not dp or dp["status"] != "approved":
                    raise PermissionError(f"Your delivery partner account is {dp['status'] if dp else 'missing delivery profile'}.")

            cur.execute("""
                UPDATE users SET google_id = ?, profile_image = COALESCE(?, profile_image), updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (google_id, picture, existing["id"]))
            conn.commit()
            return query_db("SELECT * FROM users WHERE id = ?", (existing["id"],), one=True)
        else:
            # New user registers via Google OAuth strictly as 'customer'
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
    session.permanent = True
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
    """Decorator requiring active session and verifying user active status in database."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required. Please sign in."}), 401
        user = query_db("SELECT id, role, is_active FROM users WHERE id = ?", (session["user_id"],), one=True)
        if not user or not user["is_active"]:
            clear_user_session()
            return jsonify({"error": "Your account has been deactivated or suspended. Please contact support."}), 403
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def roles_required(*allowed_roles):
    """Decorator strictly enforcing permitted user roles and active DB status on backend."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Authentication required."}), 401
            user = query_db("SELECT id, role, is_active FROM users WHERE id = ?", (session["user_id"],), one=True)
            if not user or not user["is_active"]:
                clear_user_session()
                return jsonify({"error": "Your account has been deactivated or suspended. Please contact support."}), 403

            user_role = session.get("role")
            authorized = AuthService.get_authorized_roles(session["user_id"])
            if user_role not in allowed_roles or user_role not in authorized:
                return jsonify({
                    "error": f"Forbidden. Role '{user_role}' does not have access to this resource.",
                    "required_roles": list(allowed_roles)
                }), 403
            g.current_user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator
