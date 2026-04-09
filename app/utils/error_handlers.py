"""
app/utils/error_handlers.py — Global HTTP Error Handlers
"""

from flask import render_template, jsonify, request


def register_error_handlers(app):
    """Attach 404 and 500 handlers that serve JSON or HTML based on Accept header."""

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": "Endpoint not found", "code": 404}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"500 error: {e}")
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": "Internal server error", "code": 500}), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": "Forbidden", "code": 403}), 403
        return render_template("errors/404.html"), 403
