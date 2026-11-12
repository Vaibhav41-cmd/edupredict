"""
app/routes/auth.py — Authentication Routes

Handles admin login/logout with rate-limiting awareness and audit logging.
"""

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from app.models.user import Admin

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Admin login page."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("login.html"), 400

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.is_active and admin.check_password(password):
            login_user(admin, remember=remember)
            admin.update_last_login()
            current_app.logger.info(
                f"Admin '{username}' logged in from {request.remote_addr}"
            )
            next_page = request.args.get("next")
            flash(f"Welcome back, {admin.username}!", "success")
            return redirect(next_page or url_for("dashboard.index"))
        else:
            current_app.logger.warning(
                f"Failed login attempt for '{username}' from {request.remote_addr}"
            )
            flash("Invalid username or password.", "danger")
            return render_template("login.html"), 401

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Log out the current admin session."""
    username = current_user.username
    logout_user()
    current_app.logger.info(f"Admin '{username}' logged out.")
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))
