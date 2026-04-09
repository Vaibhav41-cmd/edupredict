"""
app/routes/api.py — RESTful API (v1)

Clean JSON API for external integrations and AJAX calls.
All endpoints require admin session (cookie-based) or can be
extended with token auth for external consumers.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from datetime import datetime

from app import db
from app.models.student import Student, PredictionLog
from app.services.ml_service import ml_service
from app.utils.validators import validate_student_form, sanitize_string

api_bp = Blueprint("api", __name__)


def success(data=None, message="OK", status=200):
    return jsonify({"success": True, "message": message, "data": data}), status


def error(message="Error", status=400, errors=None):
    return jsonify({"success": False, "message": message, "errors": errors or []}), status


# ── Health Check ───────────────────────────────────────────────────────────────

@api_bp.route("/health", methods=["GET"])
def health():
    return success({
        "status": "running",
        "model_ready": ml_service.is_ready(),
        "timestamp": datetime.utcnow().isoformat(),
    })


# ── Students ───────────────────────────────────────────────────────────────────

@api_bp.route("/students", methods=["GET"])
@login_required
def get_students():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    search = request.args.get("search", "").strip()

    query = Student.query
    if search:
        query = query.filter(
            Student.name.ilike(f"%{search}%") |
            Student.student_id.ilike(f"%{search}%")
        )

    pag = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success({
        "students": [s.to_dict(include_predictions=True) for s in pag.items],
        "total": pag.total,
        "pages": pag.pages,
        "current_page": pag.page,
    })


@api_bp.route("/students/<int:student_id>", methods=["GET"])
@login_required
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    return success(student.to_dict(include_predictions=True))


@api_bp.route("/students/<int:student_id>/predict", methods=["POST"])
@login_required
def predict_for_student(student_id):
    """Re-run prediction for an existing student."""
    student = Student.query.get_or_404(student_id)

    if not ml_service.is_ready():
        return error("ML model not loaded. Run ml/train.py first.", 503)

    try:
        pred = ml_service.predict(student.feature_vector())
        log = PredictionLog(
            student_id=student.id,
            result=pred["result"],
            pass_probability=pred["pass_probability"],
            fail_probability=pred["fail_probability"],
            model_name=pred["model_name"],
            model_version=pred["model_version"],
        )
        db.session.add(log)
        db.session.commit()
        return success(pred, message="Prediction completed.")
    except Exception as e:
        current_app.logger.error(f"API prediction error: {e}")
        return error(str(e), 500)


# ── Quick Predict (no DB storage) ─────────────────────────────────────────────

@api_bp.route("/predict/quick", methods=["POST"])
@login_required
def quick_predict():
    """
    Run a one-off prediction without storing a student record.
    Useful for the 'Try it now' form on the frontend.
    """
    data = request.get_json(silent=True) or request.form.to_dict()

    if not ml_service.is_ready():
        return error("ML model not loaded.", 503)

    required = [
        "subject1_marks", "subject2_marks", "subject3_marks",
        "subject4_marks", "subject5_marks", "internal_marks",
        "attendance_pct", "study_hours_per_day",
        "assignments_submitted", "previous_backlogs",
    ]

    try:
        values = {k: float(data[k]) for k in required}
    except (KeyError, ValueError, TypeError) as e:
        return error(f"Missing or invalid field: {e}", 400)

    marks = [values[f"subject{i}_marks"] for i in range(1, 6)]
    avg = sum(marks) / 5

    feature_vector = [
        values["subject1_marks"], values["subject2_marks"],
        values["subject3_marks"], values["subject4_marks"],
        values["subject5_marks"], values["internal_marks"],
        values["attendance_pct"], values["study_hours_per_day"],
        values["assignments_submitted"], values["previous_backlogs"],
        avg,
    ]

    try:
        result = ml_service.predict(feature_vector)
        return success(result, "Quick prediction completed.")
    except Exception as e:
        return error(str(e), 500)


# ── ML Metrics ─────────────────────────────────────────────────────────────────

@api_bp.route("/model/metrics", methods=["GET"])
@login_required
def model_metrics():
    metrics = ml_service.get_metrics()
    comparison = ml_service.get_model_comparison()
    return success({
        "metrics": metrics,
        "comparison": comparison,
        "model_ready": ml_service.is_ready(),
    })


# ── Dashboard Stats ────────────────────────────────────────────────────────────

@api_bp.route("/stats/summary", methods=["GET"])
@login_required
def stats_summary():
    total = Student.query.count()
    predictions = PredictionLog.query.count()
    passes = PredictionLog.query.filter_by(result="PASS").count()
    fails = PredictionLog.query.filter_by(result="FAIL").count()

    return success({
        "total_students": total,
        "total_predictions": predictions,
        "pass_count": passes,
        "fail_count": fails,
        "pass_rate": round((passes / predictions * 100) if predictions else 0, 1),
    })
