"""
MediApp Application Factory.
Initializes Flask, binds database lifecycle, registers modular Blueprints,
and configures global error handlers and SPA routing.
"""
import os
import logging
from flask import Flask, render_template, send_from_directory, jsonify, request
from app.config import get_config, Config
from app.database import close_db, init_db

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logger = logging.getLogger("mediapp")

def create_app(config_class=None) -> Flask:
    """Application factory for MediApp."""
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    # 1. Load Configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # 2. Ensure Upload and Storage Directories Exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # 3. Register Database Teardown Handler
    app.teardown_appcontext(close_db)

    # 4. Register All Modular Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.medicine_routes import medicine_bp
    from app.routes.cart_routes import cart_bp
    from app.routes.order_routes import order_bp
    from app.routes.pharmacy_routes import pharmacy_bp
    from app.routes.delivery_routes import delivery_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.payment_routes import payment_bp
    from app.routes.prescription_routes import prescription_bp
    from app.routes.ai_routes import ai_bp
    from app.routes.health_routes import health_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(medicine_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(pharmacy_bp)
    app.register_blueprint(delivery_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(prescription_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(health_bp)

    # 5. Global API Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Bad Request", "details": str(e)}), 400
        return "Bad Request", 400

    @app.errorhandler(401)
    def unauthorized(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Unauthorized. Please log in."}), 401
        return "Unauthorized", 401

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Forbidden. Insufficient permissions."}), 403
        return "Forbidden", 403

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found."}), 404
        # For browser navigation, fallback to SPA index.html
        return render_template("index.html")

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal Server Error on {request.path}: {str(e)}")
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Internal Server Error. Please retry or contact support.",
                "status": "error"
            }), 500
        return "Internal Server Error", 500

    # 6. Single Page Application (SPA) Root Route
    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    return app
