"""
app/routes/dashboard.py — Admin Dashboard Routes

Aggregates stats from DB + ML metrics for the overview page.
"""

from flask import Blueprint, render_template, current_app
from flask_login import login_required

from app import db
from app.models.student import Student, PredictionLog
from app.services.ml_service import ml_service

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    """Main admin dashboard."""
    try:
        # ── Student Stats ──────────────────────────────────────────────────────
        total_students = Student.query.count()
        total_predictions = PredictionLog.query.count()

        pass_count = PredictionLog.query.filter_by(result="PASS").count()
        fail_count = PredictionLog.query.filter_by(result="FAIL").count()

        # ── Attendance buckets for chart ───────────────────────────────────────
        att_data = _attendance_distribution()

        # ── Recent predictions ─────────────────────────────────────────────────
        recent = (
            db.session.query(PredictionLog, Student)
            .join(Student, PredictionLog.student_id == Student.id)
            .order_by(PredictionLog.predicted_at.desc())
            .limit(10)
            .all()
        )
        recent_list = [
            {
                "student_name": s.name,
                "student_id": s.student_id,
                "result": p.result,
                "pass_probability": round(p.pass_probability * 100, 1),
                "model_name": p.model_name,
                "predicted_at": p.predicted_at.strftime("%d %b %Y %H:%M"),
            }
            for p, s in recent
        ]

        # ── ML Metrics ────────────────────────────────────────────────────────
        ml_metrics = ml_service.get_metrics()
        model_comparison = ml_service.get_model_comparison()
        cm_data = ml_service.get_confusion_matrix()

        # Marks distribution for chart
        avg_marks_data = _avg_marks_distribution()

        context = {
            "total_students": total_students,
            "total_predictions": total_predictions,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_rate": round((pass_count / total_predictions * 100) if total_predictions else 0, 1),
            "recent_predictions": recent_list,
            "ml_metrics": ml_metrics,
            "model_comparison": model_comparison,
            "confusion_matrix": cm_data,
            "attendance_distribution": att_data,
            "avg_marks_distribution": avg_marks_data,
            "model_ready": ml_service.is_ready(),
        }

        return render_template("dashboard.html", **context)

    except Exception as e:
        current_app.logger.error(f"Dashboard error: {e}")
        return render_template("dashboard.html", error=str(e), model_ready=False)


def _attendance_distribution() -> dict:
    """Bucket students by attendance range."""
    students = Student.query.with_entities(
        Student.attendance_pct, Student.id
    ).all()

    buckets = {"<50": 0, "50-60": 0, "60-75": 0, "75-90": 0, "90+": 0}
    for att, _ in students:
        if att < 50:
            buckets["<50"] += 1
        elif att < 60:
            buckets["50-60"] += 1
        elif att < 75:
            buckets["60-75"] += 1
        elif att < 90:
            buckets["75-90"] += 1
        else:
            buckets["90+"] += 1
    return buckets


def _avg_marks_distribution() -> dict:
    """Bucket students by average marks range."""
    students = Student.query.with_entities(
        Student.subject1_marks, Student.subject2_marks,
        Student.subject3_marks, Student.subject4_marks,
        Student.subject5_marks,
    ).all()

    buckets = {"<40": 0, "40-55": 0, "55-70": 0, "70-85": 0, "85+": 0}
    for row in students:
        avg = sum(row) / 5
        if avg < 40:
            buckets["<40"] += 1
        elif avg < 55:
            buckets["40-55"] += 1
        elif avg < 70:
            buckets["55-70"] += 1
        elif avg < 85:
            buckets["70-85"] += 1
        else:
            buckets["85+"] += 1
    return buckets
