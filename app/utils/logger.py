"""
app/utils/logger.py — Centralized Logging Configuration

Sets up rotating file + console logging with configurable level.
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logging(app) -> None:
    """Configure logging for Flask app: console + rotating file handler."""

    log_dir = app.config.get("LOG_DIR", "logs")
    log_level_str = app.config.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    os.makedirs(log_dir, exist_ok=True)

    # ── Formatter ──────────────────────────────────────────────────────────────
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-8s | %(module)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Rotating File Handler ─────────────────────────────────────────────────
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "app.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # ── Console Handler ────────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # ── Attach to Flask app logger ─────────────────────────────────────────────
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)

    # ── Quiet noisy libraries ──────────────────────────────────────────────────
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    app.logger.info(f"Logging initialized at level={log_level_str}, dir={log_dir}")


def get_logger(name: str) -> logging.Logger:
    """Get a named logger (for use outside Flask context)."""
    return logging.getLogger(name)
