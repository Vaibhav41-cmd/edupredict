"""
app/routes/predictions.py — Prediction History & Reports
"""

from flask import Blueprint, render_template, request, current_app
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.models.student import Student, PredictionLog

predictions_bp = Blueprint("predictions", __name__, url_prefix="/predictions")


@predictions_bp.route("/")
@login_required
def list_predictions():
    page = request.args.get("page", 1, type=int)
    result_filter = request.args.get("result", "").upper()

    query = (
        db.session.query(PredictionLog, Student)
        .join(Student, PredictionLog.student_id == Student.id)
    )

    if result_filter in ("PASS", "FAIL"):
        query = query.filter(PredictionLog.result == result_filter)

    pagination = query.order_by(PredictionLog.predicted_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    rows = [
        {
            "prediction": p.to_dict(),
            "student": {
                "name": s.name,
                "student_id": s.student_id,
                "department": s.department,
                "id": s.id,
            },
        }
        for p, s in pagination.items
    ]

    return render_template(
        "predictions/list.html",
        rows=rows,
        pagination=pagination,
        result_filter=result_filter,
    )
