"""
MediApp Configuration Module.
Provides environment-aware configuration with explicit validation for demo vs real modes.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Base application configuration."""
    BASE_DIR = BASE_DIR
    APP_ENV = os.getenv("APP_ENV", "development").lower()
    APP_MODE = os.getenv("APP_MODE", "demo").lower()
    
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production_8941fba0e3d")
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "127.0.0.1")
    
    # Database
    DB_NAME = os.getenv("DATABASE_PATH", "mediapp.db")
    DATABASE_PATH = str(BASE_DIR / DB_NAME if not os.path.isabs(DB_NAME) else DB_NAME)
    
    # Uploads
    UPLOAD_FOLDER = str(BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads/prescriptions"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)) # 16MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}
    
    # Session cookie settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # True in production HTTPS
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # External Integrations
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/api/auth/google/callback").strip()
    
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "").strip()
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "").strip()
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "").strip()

    @classmethod
    def is_demo(cls) -> bool:
        return cls.APP_MODE == "demo"

    @classmethod
    def get_public_capabilities(cls) -> dict:
        """Returns safe capability flags to the frontend without leaking secrets."""
        return {
            "app_env": cls.APP_ENV,
            "app_mode": cls.APP_MODE,
            "is_demo": cls.is_demo(),
            "google_oauth_configured": bool(cls.GOOGLE_CLIENT_ID and cls.GOOGLE_CLIENT_SECRET),
            "razorpay_configured": bool(cls.RAZORPAY_KEY_ID and cls.RAZORPAY_KEY_SECRET),
            "gemini_configured": bool(cls.GEMINI_API_KEY),
            "tesseract_configured": bool(cls.TESSERACT_CMD),
            "max_upload_size_mb": cls.MAX_CONTENT_LENGTH // (1024 * 1024)
        }

    @classmethod
    def validate_config(cls) -> list[str]:
        """Validates configuration and returns a list of warnings or fatal errors."""
        issues = []
        if cls.APP_MODE not in ("demo", "real"):
            issues.append(f"Invalid APP_MODE '{cls.APP_MODE}'. Must be 'demo' or 'real'.")
            
        if cls.APP_MODE == "real":
            if not cls.RAZORPAY_KEY_ID or not cls.RAZORPAY_KEY_SECRET:
                issues.append("APP_MODE is 'real' but RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET is missing.")
            if not cls.GEMINI_API_KEY:
                issues.append("APP_MODE is 'real' but GEMINI_API_KEY is missing for AI assistant.")
            if not cls.GOOGLE_CLIENT_ID or not cls.GOOGLE_CLIENT_SECRET:
                issues.append("APP_MODE is 'real' but GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is missing for Google OAuth.")
        return issues


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    DB_NAME = "test_mediapp.db"
    DATABASE_PATH = str(Config.BASE_DIR / "test_mediapp.db")
    APP_MODE = "demo"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}

def get_config(env_name: str = None) -> type[Config]:
    env = (env_name or os.getenv("APP_ENV", "development")).lower()
    return CONFIG_MAP.get(env, DevelopmentConfig)
