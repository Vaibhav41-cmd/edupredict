"""
app/routes/students.py — Student CRUD Routes

Full Create/Read/Update/Delete for student records.
"""

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, current_app, jsonify
)
from flask_login import login_required

from app import db
from app.models.student import Student, PredictionLog
from app.utils.validators import validate_student_form, sanitize_string
from app.services.ml_service import ml_service

students_bp = Blueprint("students", __name__, url_prefix="/students")


def _extract_form_data(form) -> dict:
    return {
        "student_id": sanitize_string(form.get("student_id", "")),
        "name": sanitize_string(form.get("name", "")),
        "email": sanitize_string(form.get("email", "")),
        "department": sanitize_string(form.get("department", "")),
        "semester": form.get("semester", 0),
        "subject1_marks": form.get("subject1_marks", 0),
        "subject2_marks": form.get("subject2_marks", 0),
        "subject3_marks": form.get("subject3_marks", 0),
        "subject4_marks": form.get("subject4_marks", 0),
        "subject5_marks": form.get("subject5_marks", 0),
        "internal_marks": form.get("internal_marks", 0),
        "attendance_pct": form.get("attendance_pct", 0),
        "study_hours_per_day": form.get("study_hours_per_day", 0),
        "assignments_submitted": form.get("assignments_submitted", 0),
        "previous_backlogs": form.get("previous_backlogs", 0),
    }


@students_bp.route("/")
@login_required
def list_students():
    """Paginated list of all students with their latest prediction."""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    dept_filter = request.args.get("department", "").strip()

    query = Student.query

    if search:
        query = query.filter(
            Student.name.ilike(f"%{search}%") |
            Student.student_id.ilike(f"%{search}%") |
            Student.email.ilike(f"%{search}%")
        )
    if dept_filter:
        query = query.filter_by(department=dept_filter)

    pagination = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    # All unique departments for filter dropdown
    departments = [r[0] for r in db.session.query(Student.department).distinct().all()]

    return render_template(
        "students/list.html",
        students=pagination.items,
        pagination=pagination,
        search=search,
        departments=departments,
        selected_dept=dept_filter,
    )


@students_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_student():
    """Add a new student and run ML prediction."""
    if request.method == "POST":
        data = _extract_form_data(request.form)
        is_valid, errors = validate_student_form(data)

        if not is_valid:
            for err in errors:
                flash(err, "danger")
            return render_template("students/add.html", form_data=data), 400

        # Check duplicate
        if Student.query.filter_by(student_id=data["student_id"].upper()).first():
            flash(f"Student ID '{data['student_id']}' already exists.", "danger")
            return render_template("students/add.html", form_data=data), 400

        if Student.query.filter_by(email=data["email"].lower()).first():
            flash(f"Email '{data['email']}' already registered.", "danger")
            return render_template("students/add.html", form_data=data), 400

        try:
            # Compute average
            marks = [float(data[f"subject{i}_marks"]) for i in range(1, 6)]
            avg = sum(marks) / 5

            student = Student(
                student_id=data["student_id"].upper(),
                name=data["name"],
                email=data["email"].lower(),
                department=data["department"],
                semester=int(data["semester"]),
                subject1_marks=float(data["subject1_marks"]),
                subject2_marks=float(data["subject2_marks"]),
                subject3_marks=float(data["subject3_marks"]),
                subject4_marks=float(data["subject4_marks"]),
                subject5_marks=float(data["subject5_marks"]),
                internal_marks=float(data["internal_marks"]),
                attendance_pct=float(data["attendance_pct"]),
                study_hours_per_day=float(data["study_hours_per_day"]),
                assignments_submitted=int(data["assignments_submitted"]),
                previous_backlogs=int(data["previous_backlogs"]),
            )

            db.session.add(student)
            db.session.flush()  # get student.id before commit

            # Run ML prediction
            prediction_result = None
            if ml_service.is_ready():
                feature_vec = student.feature_vector()
                pred = ml_service.predict(feature_vec)

                log = PredictionLog(
                    student_id=student.id,
                    result=pred["result"],
                    pass_probability=pred["pass_probability"],
                    fail_probability=pred["fail_probability"],
                    model_name=pred["model_name"],
                    model_version=pred["model_version"],
                    feature_snapshot=dict(zip(
                        ["s1","s2","s3","s4","s5","internal","attendance","study_hrs","assignments","backlogs","avg"],
                        feature_vec
                    )),
                )
                db.session.add(log)
                prediction_result = pred

            db.session.commit()
            current_app.logger.info(f"Student {student.student_id} added. Prediction: {prediction_result}")

            flash(f"Student '{student.name}' added successfully!", "success")
            return redirect(url_for("students.view_student", student_id=student.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding student: {e}")
            flash(f"An error occurred: {str(e)}", "danger")
            return render_template("students/add.html", form_data=data), 500

    return render_template("students/add.html", form_data={})


@students_bp.route("/<int:student_id>")
@login_required
def view_student(student_id: int):
    """View a single student's full profile and prediction history."""
    student = Student.query.get_or_404(student_id)
    predictions = (
        student.predictions.order_by(PredictionLog.predicted_at.desc()).all()
    )
    return render_template("students/view.html", student=student, predictions=predictions)


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id: int):
    """Edit student academic data and re-run prediction."""
    student = Student.query.get_or_404(student_id)

    if request.method == "POST":
        data = _extract_form_data(request.form)
        is_valid, errors = validate_student_form(data)

        if not is_valid:
            for err in errors:
                flash(err, "danger")
            return render_template("students/edit.html", student=student, form_data=data), 400

        try:
            student.name = data["name"]
            student.email = data["email"].lower()
            student.department = data["department"]
            student.semester = int(data["semester"])
            student.subject1_marks = float(data["subject1_marks"])
            student.subject2_marks = float(data["subject2_marks"])
            student.subject3_marks = float(data["subject3_marks"])
            student.subject4_marks = float(data["subject4_marks"])
            student.subject5_marks = float(data["subject5_marks"])
            student.internal_marks = float(data["internal_marks"])
            student.attendance_pct = float(data["attendance_pct"])
            student.study_hours_per_day = float(data["study_hours_per_day"])
            student.assignments_submitted = int(data["assignments_submitted"])
            student.previous_backlogs = int(data["previous_backlogs"])

            # Re-run prediction
            if ml_service.is_ready():
                feature_vec = student.feature_vector()
                pred = ml_service.predict(feature_vec)
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
            flash("Student record updated and re-predicted.", "success")
            return redirect(url_for("students.view_student", student_id=student.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating student {student_id}: {e}")
            flash(f"Update failed: {str(e)}", "danger")

    return render_template("students/edit.html", student=student, form_data=student.to_dict())


@students_bp.route("/<int:student_id>/delete", methods=["POST"])
@login_required
def delete_student(student_id: int):
    """Soft delete (hard delete) a student record."""
    student = Student.query.get_or_404(student_id)
    try:
        db.session.delete(student)
        db.session.commit()
        current_app.logger.info(f"Student {student.student_id} deleted.")
        flash(f"Student '{student.name}' deleted.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Delete failed: {str(e)}", "danger")
    return redirect(url_for("students.list_students"))
