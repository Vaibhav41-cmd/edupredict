"""
app/utils/validators.py — Centralized Input Validation

Validates and sanitizes all student form inputs before DB/ML operations.
"""

import re
from typing import Tuple, Optional


# ── Constants ──────────────────────────────────────────────────────────────────
MARK_MIN, MARK_MAX = 0.0, 100.0
INTERNAL_MAX = 50.0
ATTENDANCE_MIN, ATTENDANCE_MAX = 0.0, 100.0
STUDY_HOURS_MIN, STUDY_HOURS_MAX = 0.0, 18.0
ASSIGNMENTS_MIN, ASSIGNMENTS_MAX = 0, 10
BACKLOGS_MIN, BACKLOGS_MAX = 0, 20
SEMESTER_MIN, SEMESTER_MAX = 1, 8


def validate_marks(value: float, field_name: str) -> Tuple[bool, Optional[str]]:
    """Validate subject marks (0–100)."""
    if not isinstance(value, (int, float)):
        return False, f"{field_name} must be a number."
    if not (MARK_MIN <= float(value) <= MARK_MAX):
        return False, f"{field_name} must be between {MARK_MIN} and {MARK_MAX}."
    return True, None


def validate_internal_marks(value: float) -> Tuple[bool, Optional[str]]:
    if not isinstance(value, (int, float)):
        return False, "Internal marks must be a number."
    if not (MARK_MIN <= float(value) <= INTERNAL_MAX):
        return False, f"Internal marks must be between 0 and {INTERNAL_MAX}."
    return True, None


def validate_attendance(value: float) -> Tuple[bool, Optional[str]]:
    if not isinstance(value, (int, float)):
        return False, "Attendance must be a number."
    if not (ATTENDANCE_MIN <= float(value) <= ATTENDANCE_MAX):
        return False, f"Attendance must be between {ATTENDANCE_MIN}% and {ATTENDANCE_MAX}%."
    return True, None


def validate_study_hours(value: float) -> Tuple[bool, Optional[str]]:
    if not isinstance(value, (int, float)):
        return False, "Study hours must be a number."
    if not (STUDY_HOURS_MIN <= float(value) <= STUDY_HOURS_MAX):
        return False, f"Study hours must be between {STUDY_HOURS_MIN} and {STUDY_HOURS_MAX}."
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    if not re.match(pattern, email.strip()):
        return False, "Invalid email address format."
    return True, None


def validate_student_id(sid: str) -> Tuple[bool, Optional[str]]:
    pattern = r"^[A-Z0-9]{4,20}$"
    if not re.match(pattern, sid.strip().upper()):
        return False, "Student ID must be 4–20 uppercase alphanumeric characters."
    return True, None


def validate_student_form(data: dict) -> Tuple[bool, list]:
    """
    Master validation function for all student form fields.
    Returns (is_valid, list_of_error_messages).
    """
    errors = []

    # Required string fields
    for field in ["name", "email", "student_id", "department"]:
        if not data.get(field) or not str(data[field]).strip():
            errors.append(f"'{field}' is required.")

    # Email
    if data.get("email"):
        ok, msg = validate_email(data["email"])
        if not ok:
            errors.append(msg)

    # Student ID
    if data.get("student_id"):
        ok, msg = validate_student_id(data["student_id"])
        if not ok:
            errors.append(msg)

    # Semester
    try:
        sem = int(data.get("semester", 0))
        if not (SEMESTER_MIN <= sem <= SEMESTER_MAX):
            errors.append(f"Semester must be between {SEMESTER_MIN} and {SEMESTER_MAX}.")
    except (ValueError, TypeError):
        errors.append("Semester must be an integer.")

    # Subject marks
    for i in range(1, 6):
        key = f"subject{i}_marks"
        try:
            val = float(data.get(key, -1))
            ok, msg = validate_marks(val, f"Subject {i} marks")
            if not ok:
                errors.append(msg)
        except (ValueError, TypeError):
            errors.append(f"Subject {i} marks must be a valid number.")

    # Internal marks
    try:
        ok, msg = validate_internal_marks(float(data.get("internal_marks", -1)))
        if not ok:
            errors.append(msg)
    except (ValueError, TypeError):
        errors.append("Internal marks must be a valid number.")

    # Attendance
    try:
        ok, msg = validate_attendance(float(data.get("attendance_pct", -1)))
        if not ok:
            errors.append(msg)
    except (ValueError, TypeError):
        errors.append("Attendance must be a valid number.")

    # Study hours
    try:
        ok, msg = validate_study_hours(float(data.get("study_hours_per_day", -1)))
        if not ok:
            errors.append(msg)
    except (ValueError, TypeError):
        errors.append("Study hours must be a valid number.")

    # Assignments
    try:
        val = int(data.get("assignments_submitted", -1))
        if not (ASSIGNMENTS_MIN <= val <= ASSIGNMENTS_MAX):
            errors.append(f"Assignments must be between {ASSIGNMENTS_MIN} and {ASSIGNMENTS_MAX}.")
    except (ValueError, TypeError):
        errors.append("Assignments submitted must be an integer.")

    # Backlogs
    try:
        val = int(data.get("previous_backlogs", -1))
        if not (BACKLOGS_MIN <= val <= BACKLOGS_MAX):
            errors.append(f"Backlogs must be between {BACKLOGS_MIN} and {BACKLOGS_MAX}.")
    except (ValueError, TypeError):
        errors.append("Previous backlogs must be an integer.")

    return len(errors) == 0, errors


def sanitize_string(value: str, max_length: int = 200) -> str:
    """Strip and truncate a string safely."""
    return str(value).strip()[:max_length]
