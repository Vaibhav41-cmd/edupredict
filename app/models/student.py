"""
app/models/student.py — Student and Prediction Models

Two tightly coupled models:
  - Student      : stores academic profile data
  - PredictionLog: stores every ML prediction made for a student
"""

from datetime import datetime
from app import db


class Student(db.Model):
    """
    Core student academic record.
    Each student has one profile and potentially many predictions.
    """

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False)

    # ── Academic Features (ML inputs) ─────────────────────────────────────────
    subject1_marks = db.Column(db.Float, nullable=False)   # 0–100
    subject2_marks = db.Column(db.Float, nullable=False)
    subject3_marks = db.Column(db.Float, nullable=False)
    subject4_marks = db.Column(db.Float, nullable=False)
    subject5_marks = db.Column(db.Float, nullable=False)
    internal_marks = db.Column(db.Float, nullable=False)   # 0–50
    attendance_pct = db.Column(db.Float, nullable=False)   # 0–100
    study_hours_per_day = db.Column(db.Float, nullable=False)  # 0–24
    assignments_submitted = db.Column(db.Integer, nullable=False)  # 0–10
    previous_backlogs = db.Column(db.Integer, nullable=False, default=0)

    # ── Metadata ──────────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relationship ──────────────────────────────────────────────────────────
    predictions = db.relationship(
        "PredictionLog",
        backref="student",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # ── Computed Properties ───────────────────────────────────────────────────

    @property
    def average_marks(self) -> float:
        marks = [
            self.subject1_marks,
            self.subject2_marks,
            self.subject3_marks,
            self.subject4_marks,
            self.subject5_marks,
        ]
        return round(sum(marks) / len(marks), 2)

    @property
    def latest_prediction(self):
        return (
            self.predictions.order_by(PredictionLog.predicted_at.desc()).first()
        )

    def feature_vector(self) -> list:
        """Return ordered feature list matching ML model training order."""
        return [
            self.subject1_marks,
            self.subject2_marks,
            self.subject3_marks,
            self.subject4_marks,
            self.subject5_marks,
            self.internal_marks,
            self.attendance_pct,
            self.study_hours_per_day,
            self.assignments_submitted,
            self.previous_backlogs,
            self.average_marks,
        ]

    def to_dict(self, include_predictions: bool = False) -> dict:
        data = {
            "id": self.id,
            "student_id": self.student_id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "semester": self.semester,
            "subject1_marks": self.subject1_marks,
            "subject2_marks": self.subject2_marks,
            "subject3_marks": self.subject3_marks,
            "subject4_marks": self.subject4_marks,
            "subject5_marks": self.subject5_marks,
            "internal_marks": self.internal_marks,
            "attendance_pct": self.attendance_pct,
            "study_hours_per_day": self.study_hours_per_day,
            "assignments_submitted": self.assignments_submitted,
            "previous_backlogs": self.previous_backlogs,
            "average_marks": self.average_marks,
            "created_at": self.created_at.isoformat(),
        }
        if include_predictions:
            pred = self.latest_prediction
            data["latest_prediction"] = pred.to_dict() if pred else None
        return data

    def __repr__(self) -> str:
        return f"<Student {self.student_id} — {self.name}>"


class PredictionLog(db.Model):
    """
    Immutable audit log of every ML prediction.
    Stores the result, probability, and which model version was used.
    """

    __tablename__ = "prediction_logs"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )

    # ── Prediction Output ─────────────────────────────────────────────────────
    result = db.Column(db.Enum("PASS", "FAIL"), nullable=False)
    pass_probability = db.Column(db.Float, nullable=False)   # 0.0–1.0
    fail_probability = db.Column(db.Float, nullable=False)

    # ── Model Context ─────────────────────────────────────────────────────────
    model_name = db.Column(db.String(100), nullable=False)
    model_version = db.Column(db.String(50), nullable=True)

    # ── Snapshot of features at prediction time ────────────────────────────────
    feature_snapshot = db.Column(db.JSON, nullable=True)

    predicted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "result": self.result,
            "pass_probability": round(self.pass_probability * 100, 1),
            "fail_probability": round(self.fail_probability * 100, 1),
            "model_name": self.model_name,
            "model_version": self.model_version,
            "predicted_at": self.predicted_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<PredictionLog student={self.student_id} result={self.result}>"
