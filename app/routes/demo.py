"""
app/routes/demo.py — Interactive Live Demo & Viva Showcase Routes

Provides:
  - /demo                      : Public & Admin interactive ML prediction sandbox
  - /demo/api/predict          : Real-time ML inference endpoint with academic advice
  - /demo/login/admin          : One-click Admin demo login (when DEMO_MODE=True)
  - /demo/login/student/<sid>  : One-click Student Portal demo login (when DEMO_MODE=True)
  - /demo/reset                : Reset demo database back to clean 30-student state
  - /demo/report/<fmt>         : Download MCA-521 Project Report (.docx or .pdf)
"""

import os
from datetime import datetime
from flask import (
    Blueprint, render_template, request, jsonify,
    redirect, url_for, flash, session, current_app, send_file, abort
)
from flask_login import login_user, login_required

from app import db
from app.models.user import Admin
from app.models.student import Student, PredictionLog
from app.models.student_auth import StudentAuth
from app.services.ml_service import ml_service
from app.services.demo_service import reset_demo_data

demo_bp = Blueprint("demo", __name__, url_prefix="/demo")


def _build_recommendations(values: dict, avg_marks: float, pred_result: str) -> list:
    tips = []
    att = values["attendance_pct"]
    internal = values["internal_marks"]
    hrs = values["study_hours_per_day"]
    assign = int(values["assignments_submitted"])
    backlogs = int(values["previous_backlogs"])

    if att < 75:
        tips.append(
            f"Attendance is {att:.1f}% (below mandatory 75% norm). Attend upcoming lectures consistently to gain +{75 - att:.1f}%."
        )
    else:
        tips.append(f"Attendance ({att:.1f}%) meets institutional requirements — maintain regularity.")

    if avg_marks < 50:
        tips.append(
            f"Subject average is {avg_marks:.1f}/100. Prioritize remedial tutorials and solve previous university question papers."
        )
    elif avg_marks >= 75:
        tips.append(f"Strong subject average ({avg_marks:.1f}/100) — on track for First Class with Distinction.")

    if internal < 30:
        tips.append(
            f"Internal assessment ({internal:.1f}/50) is low. Focus on lab journals, mid-term tests, and timely submissions."
        )

    if hrs < 3.5:
        tips.append(
            f"Self-study duration ({hrs:.1f} hrs/day) should be increased to at least 4.0–5.0 hrs/day for MCA coursework."
        )

    if assign < 7:
        tips.append(f"Only {assign}/10 assignments submitted. Complete pending practical & theory assignments.")

    if backlogs > 0:
        tips.append(f"Clear {backlogs} active backlog(s) through structured weekly revision slots.")

    if pred_result == "FAIL":
        tips.append("Immediate Action: Schedule faculty mentor counseling & trigger early academic alert.")

    return tips


@demo_bp.route("/")
def index():
    """Interactive Live Demo & Quick Predictor showcase page."""
    total_students = Student.query.count()
    total_predictions = PredictionLog.query.count()
    pass_count = PredictionLog.query.filter_by(result="PASS").count()
    fail_count = PredictionLog.query.filter_by(result="FAIL").count()

    ml_metrics = ml_service.get_metrics() if ml_service.is_ready() else {}
    model_comparison = ml_service.get_model_comparison() if ml_service.is_ready() else []

    report_dir = current_app.config.get("REPORT_DIR", "report")
    has_docx = os.path.exists(os.path.join(report_dir, "EduPredict_MCA521_Project_Report.docx"))
    has_pdf = os.path.exists(os.path.join(report_dir, "EduPredict_MCA521_Project_Report.pdf"))

    return render_template(
        "demo.html",
        total_students=total_students,
        total_predictions=total_predictions,
        pass_count=pass_count,
        fail_count=fail_count,
        pass_rate=round((pass_count / total_predictions * 100) if total_predictions else 0, 1),
        ml_metrics=ml_metrics,
        model_comparison=model_comparison,
        model_ready=ml_service.is_ready(),
        demo_mode=current_app.config.get("DEMO_MODE", False),
        has_docx=has_docx,
        has_pdf=has_pdf,
    )


@demo_bp.route("/api/predict", methods=["POST"])
def api_predict():
    """Run real-time ML prediction for interactive demo sliders/inputs."""
    data = request.get_json(silent=True) or request.form.to_dict()

    if not ml_service.is_ready():
        return jsonify({"success": False, "message": "ML model is not trained yet."}), 503

    required = [
        "subject1_marks", "subject2_marks", "subject3_marks",
        "subject4_marks", "subject5_marks", "internal_marks",
        "attendance_pct", "study_hours_per_day",
        "assignments_submitted", "previous_backlogs",
    ]

    try:
        values = {k: float(data[k]) for k in required}
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"success": False, "message": f"Invalid input: {exc}"}), 400

    # Clamp to valid academic bounds
    for i in range(1, 6):
        values[f"subject{i}_marks"] = max(0.0, min(100.0, values[f"subject{i}_marks"]))
    values["internal_marks"] = max(0.0, min(50.0, values["internal_marks"]))
    values["attendance_pct"] = max(0.0, min(100.0, values["attendance_pct"]))
    values["study_hours_per_day"] = max(0.0, min(18.0, values["study_hours_per_day"]))
    values["assignments_submitted"] = max(0.0, min(10.0, round(values["assignments_submitted"])))
    values["previous_backlogs"] = max(0.0, min(20.0, round(values["previous_backlogs"])))

    marks = [values[f"subject{i}_marks"] for i in range(1, 6)]
    avg = round(sum(marks) / 5.0, 2)

    feature_vec = [
        values["subject1_marks"], values["subject2_marks"],
        values["subject3_marks"], values["subject4_marks"],
        values["subject5_marks"], values["internal_marks"],
        values["attendance_pct"], values["study_hours_per_day"],
        values["assignments_submitted"], values["previous_backlogs"],
        avg,
    ]

    pred = ml_service.predict(feature_vec)
    tips = _build_recommendations(values, avg, pred["result"])

    return jsonify({
        "success": True,
        "data": {
            "result": pred["result"],
            "pass_probability": round(pred["pass_probability"] * 100, 2),
            "fail_probability": round(pred["fail_probability"] * 100, 2),
            "confidence_level": pred["confidence_level"],
            "model_name": pred["model_name"],
            "model_version": pred["model_version"],
            "average_marks": avg,
            "feature_importance": pred.get("feature_importance", []),
            "recommendations": tips,
        },
    })


@demo_bp.route("/login/admin", methods=["POST"])
def demo_admin_login():
    """One-click Admin login for Demo Mode."""
    if not current_app.config.get("DEMO_MODE", False):
        flash("One-click demo login is only enabled in Demo Mode.", "warning")
        return redirect(url_for("auth.login"))

    admin = Admin.query.filter_by(username="admin").first()
    if not admin:
        flash("Demo admin account not found.", "danger")
        return redirect(url_for("auth.login"))

    login_user(admin)
    admin.update_last_login()
    flash("Logged into Admin Panel in Interactive Demo Mode!", "success")
    return redirect(url_for("dashboard.index"))


@demo_bp.route("/login/student/<string:student_code>", methods=["POST"])
def demo_student_login(student_code: str):
    """One-click Student Portal login for Demo Mode."""
    if not current_app.config.get("DEMO_MODE", False):
        flash("One-click demo login is only enabled in Demo Mode.", "warning")
        return redirect(url_for("student_portal.login"))

    code = student_code.strip().upper()
    auth = StudentAuth.query.filter_by(username=code).first()
    if not auth:
        student = Student.query.filter_by(student_id=code).first()
        if student:
            auth = StudentAuth(student_id=student.id, username=code, is_active=True)
            auth.set_password(code)
            db.session.add(auth)
            db.session.commit()

    if not auth or not auth.is_active:
        flash(f"Demo student account '{code}' not found.", "danger")
        return redirect(url_for("student_portal.login"))

    session["student_id"] = auth.student_id
    session["student_username"] = auth.username
    auth.last_login = datetime.utcnow()
    db.session.commit()
    flash(f"Logged into Student Portal as {auth.student.name} ({code})!", "success")
    return redirect(url_for("student_portal.dashboard"))


@demo_bp.route("/reset", methods=["POST"])
@login_required
def reset_demo():
    """Reset demo dataset back to default 30 students."""
    if not current_app.config.get("DEMO_MODE", False):
        flash("Demo reset is disabled in production MySQL mode.", "warning")
        return redirect(url_for("dashboard.index"))

    count = reset_demo_data(current_app)
    flash(f"Demo database reset cleanly with {count} sample student records & predictions!", "success")
    return redirect(url_for("dashboard.index"))


@demo_bp.route("/report/<string:fmt>")
def download_report(fmt: str):
    """Download generated MCA-521 Project Report (.docx or .pdf)."""
    report_dir = current_app.config.get("REPORT_DIR", "report")
    mapping = {
        "docx": ("EduPredict_MCA521_Project_Report.docx",
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        "pdf": ("EduPredict_MCA521_Project_Report.pdf", "application/pdf"),
        "pptx": ("EduPredict_MCA521_Presentation.pptx",
                 "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    }
    if fmt.lower() not in mapping:
        abort(404)
    filename, mimetype = mapping[fmt.lower()]
    full_path = os.path.join(report_dir, filename)
    if not os.path.exists(full_path):
        flash("Project report file is not generated yet.", "warning")
        return redirect(url_for("demo.index"))
    return send_file(full_path, mimetype=mimetype, as_attachment=True, download_name=filename)
