"""
config.py — Centralized Configuration Management
Supports Development, Testing, and Production environments.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base configuration shared across all environments."""

    # ── Flask Core ─────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    WTF_CSRF_ENABLED = True

    # ── Database ───────────────────────────────────────────────────────────────
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME", "student_prediction_db")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set True for SQL debug logging
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # ── ML ─────────────────────────────────────────────────────────────────────
    MODEL_DIR = os.getenv("MODEL_DIR", os.path.join(os.path.dirname(__file__), "ml", "saved_models"))
    BEST_MODEL_FILE = "best_model.joblib"
    SCALER_FILE = "scaler.joblib"
    METADATA_FILE = "model_metadata.joblib"

    # ── Email / Alerts ─────────────────────────────────────────────────────────
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
    APP_URL = os.getenv("APP_URL", "http://localhost:5000")

    # ── Logging ────────────────────────────────────────────────────────────────
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # ── Pagination ─────────────────────────────────────────────────────────────
    STUDENTS_PER_PAGE = 15


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = False
    LOG_LEVEL = "DEBUG"


class TestingConfig(BaseConfig):
    TESTING = True
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
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    return config_map.get(env, DevelopmentConfig)
