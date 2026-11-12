"""
config.py — Centralized Configuration Management
Supports Development, Demo (SQLite), Testing, and Production environments.
Automatically falls back to SQLite Demo Mode when MySQL/XAMPP is not running.
"""

import os
import socket
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _is_mysql_reachable(host: str, port: int, timeout: float = 0.4) -> bool:
    """Fast TCP check to detect whether a local/remote MySQL server is listening."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _build_database_config():
    """
    Resolve database URI, engine options, and demo mode flag.
    Priority:
      1. Explicit DATABASE_URL environment variable
      2. Explicit DB_ENGINE=sqlite or DEMO_MODE=true -> SQLite Demo DB
      3. Explicit DB_ENGINE=mysql -> MySQL URI
      4. Auto-detect: use MySQL if reachable on DB_HOST:DB_PORT, else SQLite Demo DB
    """
    explicit_url = os.getenv("DATABASE_URL", "").strip()
    db_engine = os.getenv("DB_ENGINE", "auto").strip().lower()
    demo_env = os.getenv("DEMO_MODE", "").strip().lower()

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", 3306))
    db_name = os.getenv("DB_NAME", "student_prediction_db")
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")

    sqlite_dir = os.path.join(BASE_DIR, "database")
    os.makedirs(sqlite_dir, exist_ok=True)
    sqlite_path = os.path.join(sqlite_dir, "edupredict_demo.db")
    sqlite_uri = f"sqlite:///{sqlite_path}"
    mysql_uri = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        "?charset=utf8mb4"
    )

    if explicit_url:
        uri = explicit_url
        is_demo = demo_env in ("1", "true", "yes") or uri.startswith("sqlite")
    elif demo_env in ("1", "true", "yes") or db_engine == "sqlite":
        uri = sqlite_uri
        is_demo = True
    elif db_engine == "mysql":
        uri = mysql_uri
        is_demo = demo_env in ("1", "true", "yes")
    else:
        if _is_mysql_reachable(db_host, db_port):
            uri = mysql_uri
            is_demo = False
        else:
            uri = sqlite_uri
            is_demo = True

    if uri.startswith("sqlite"):
        engine_opts = {"connect_args": {"check_same_thread": False}}
    else:
        engine_opts = {
            "pool_recycle": 280,
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
        }

    return uri, engine_opts, is_demo


_DB_URI, _ENGINE_OPTS, _IS_DEMO = _build_database_config()


class BaseConfig:
    """Base configuration shared across all environments."""

    # ── Flask Core ─────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SSL_STRICT = False  # Allow reverse-proxy HTTPS previews cleanly
    # Arena's Live Preview may embed the app cross-site; allow the signed session
    # cookie on HTTPS preview requests so Flask-WTF can validate submitted tokens.
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "None")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() in ("1", "true", "yes")

    # ── Demo Mode Flag ─────────────────────────────────────────────────────────
    DEMO_MODE = _IS_DEMO
    SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "true").lower() in ("1", "true", "yes")

    # ── Database ───────────────────────────────────────────────────────────────
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME", "student_prediction_db")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    SQLALCHEMY_DATABASE_URI = _DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set True for SQL debug logging
    SQLALCHEMY_ENGINE_OPTIONS = _ENGINE_OPTS

    # ── ML ─────────────────────────────────────────────────────────────────────
    MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(BASE_DIR, "ml", "saved_models"))
    BEST_MODEL_FILE = "best_model.joblib"
    SCALER_FILE = "scaler.joblib"
    METADATA_FILE = "model_metadata.joblib"

    # ── Report Deliverables Directory ──────────────────────────────────────────
    REPORT_DIR = os.path.join(BASE_DIR, "report")

    # ── Email / Alerts ─────────────────────────────────────────────────────────
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
    APP_URL = os.getenv("APP_URL", "/")

    # ── Logging ────────────────────────────────────────────────────────────────
    LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # ── Pagination ─────────────────────────────────────────────────────────────
    STUDENTS_PER_PAGE = 15


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = False
    LOG_LEVEL = "INFO"


class DemoConfig(BaseConfig):
    DEBUG = True
    DEMO_MODE = True
    SEED_DEMO_DATA = True
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'edupredict_demo.db')}"
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
    LOG_LEVEL = "INFO"


class TestingConfig(BaseConfig):
    TESTING = True
    DEMO_MODE = False
    SEED_DEMO_DATA = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
    LOG_LEVEL = "DEBUG"


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    LOG_LEVEL = "WARNING"


# ── Config selector ────────────────────────────────────────────────────────────
config_map = {
    "development": DevelopmentConfig,
    "demo": DemoConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    return config_map.get(env, DevelopmentConfig)
