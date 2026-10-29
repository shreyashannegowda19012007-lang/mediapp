"""
System Health and Diagnostics Routes for MediApp.
Provides liveness and readiness probes along with safe capability discovery.
"""
from flask import Blueprint, jsonify
from datetime import datetime, timezone
from app.config import Config
from app.database import query_db

health_bp = Blueprint("health", __name__, url_prefix="/api")

@health_bp.route("/health", methods=["GET"])
def health_check():
    db_ok = False
    try:
        res = query_db("SELECT 1 as ok", one=True)
        db_ok = bool(res and res["ok"] == 1)
    except Exception:
        db_ok = False

    status_code = 200 if db_ok else 503
    return jsonify({
        "status": "healthy" if db_ok else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app_env": Config.APP_ENV,
        "app_mode": Config.APP_MODE,
        "database_connected": db_ok
    }), status_code

@health_bp.route("/diagnostics", methods=["GET"])
def diagnostics():
    """Safe diagnostic report for operators and verification suites."""
    config_issues = Config.validate_config()
    db_test = False
    try:
        res = query_db("SELECT 1 as ok", one=True)
        db_test = bool(res and res["ok"] == 1)
    except Exception:
        db_test = False

    return jsonify({
        "status": "ok" if (db_test and not config_issues) else "warning",
        "app_env": Config.APP_ENV,
        "app_mode": Config.APP_MODE,
        "database_ready": db_test,
        "config_validation": {
            "is_valid": len(config_issues) == 0,
            "issues": config_issues
        },
        "capabilities": Config.get_public_capabilities()
    })
