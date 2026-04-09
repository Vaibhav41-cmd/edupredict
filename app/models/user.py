"""
app/models/user.py — Admin User Model

Handles authentication and session management via Flask-Login.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class Admin(UserMixin, db.Model):
    """Admin user who can access the dashboard and manage predictions."""

    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # ── Password Management ────────────────────────────────────────────────────

    def set_password(self, password: str) -> None:
        """Hash and store password using Werkzeug."""
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self) -> None:
        self.last_login = datetime.utcnow()
        db.session.commit()

    # ── Flask-Login Integration ────────────────────────────────────────────────

    def get_id(self) -> str:
        return str(self.id)

    # ── Representation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def __repr__(self) -> str:
        return f"<Admin {self.username}>"
