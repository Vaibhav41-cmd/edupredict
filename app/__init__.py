"""
app/__init__.py — Flask Application Factory

Uses the Factory Pattern for clean, testable application creation.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS

from config import get_config

# ── Extensions (initialized without app) ──────────────────────────────────────
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=None):
    """
    Application factory function.
    Returns a fully configured Flask app instance.
    """
    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static",
    )

    # ── Configuration ──────────────────────────────────────────────────────────
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # ── Initialize extensions ──────────────────────────────────────────────────
    db.init_app(app)
    csrf.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Login Manager ──────────────────────────────────────────────────────────
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access the admin panel."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import Admin
        return Admin.query.get(int(user_id))

    # ── Error Handlers ─────────────────────────────────────────────────────────
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    # ── Register Blueprints ────────────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.students import students_bp
    from app.routes.predictions import predictions_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    # ── Setup Logging ──────────────────────────────────────────────────────────
    from app.utils.logger import setup_logging
    setup_logging(app)

    # ── Create DB tables ───────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_admin(app)

    app.logger.info("✅  Student Prediction System started.")
    return app


def _seed_admin(app):
    """Create default admin user if none exists."""
    import os
    from app.models.user import Admin

    if Admin.query.count() == 0:
        admin = Admin(
            username=os.getenv("ADMIN_USERNAME", "admin"),
            email=os.getenv("ADMIN_EMAIL", "admin@prediction.com"),
        )
        admin.set_password(os.getenv("ADMIN_PASSWORD", "Admin@1234"))
        from app import db as _db
        _db.session.add(admin)
        _db.session.commit()
        app.logger.info("✅  Default admin user created.")
