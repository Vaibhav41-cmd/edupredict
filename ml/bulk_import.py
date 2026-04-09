"""
ml/bulk_import.py — Bulk Student Data Importer

Reads a CSV file and inserts all student records + runs ML predictions.

Usage:
  python ml/bulk_import.py --file path/to/students.csv

CSV format (header required):
  student_id,name,email,department,semester,
  subject1_marks,subject2_marks,subject3_marks,subject4_marks,subject5_marks,
  internal_marks,attendance_pct,study_hours_per_day,assignments_submitted,previous_backlogs

Example CSV row:
  MCA2024010,Amit Verma,amit@demo.com,MCA,2,75,80,72,68,77,38,82,4.5,8,1
"""

import os
import sys
import csv
import argparse
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "student_id", "name", "email", "department", "semester",
    "subject1_marks", "subject2_marks", "subject3_marks", "subject4_marks", "subject5_marks",
    "internal_marks", "attendance_pct", "study_hours_per_day",
    "assignments_submitted", "previous_backlogs",
]


def run_import(csv_path: str):
    from app import create_app, db
    from app.models.student import Student, PredictionLog
    from app.services.ml_service import ml_service
    from app.utils.validators import validate_student_form

    app = create_app()

    if not os.path.exists(csv_path):
        logger.error(f"File not found: {csv_path}")
        sys.exit(1)

    with app.app_context():
        inserted = 0
        skipped = 0
        errors = 0

        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            # Validate headers
            missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
            if missing:
                logger.error(f"CSV missing columns: {missing}")
                sys.exit(1)

            for row_num, row in enumerate(reader, start=2):
                data = {k: v.strip() for k, v in row.items()}
                is_valid, errs = validate_student_form(data)

                if not is_valid:
                    logger.warning(f"Row {row_num}: Validation failed — {errs}")
                    errors += 1
                    continue

                sid = data["student_id"].upper()

                if Student.query.filter_by(student_id=sid).first():
                    logger.info(f"Row {row_num}: Skipping {sid} (already exists)")
                    skipped += 1
                    continue

                try:
                    marks = [float(data[f"subject{i}_marks"]) for i in range(1, 6)]
                    student = Student(
                        student_id=sid,
                        name=data["name"],
                        email=data["email"].lower(),
                        department=data["department"],
                        semester=int(data["semester"]),
                        subject1_marks=marks[0],
                        subject2_marks=marks[1],
                        subject3_marks=marks[2],
                        subject4_marks=marks[3],
                        subject5_marks=marks[4],
                        internal_marks=float(data["internal_marks"]),
                        attendance_pct=float(data["attendance_pct"]),
                        study_hours_per_day=float(data["study_hours_per_day"]),
                        assignments_submitted=int(data["assignments_submitted"]),
                        previous_backlogs=int(data["previous_backlogs"]),
                    )
                    db.session.add(student)
                    db.session.flush()

                    # Run ML prediction
                    if ml_service.is_ready():
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
                        logger.info(f"Row {row_num}: {sid} → {pred['result']} ({pred['pass_probability']*100:.1f}% pass)")
                    else:
                        logger.warning(f"Row {row_num}: {sid} inserted but ML not ready")

                    db.session.commit()
                    inserted += 1

                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Row {row_num}: DB error — {e}")
                    errors += 1

        logger.info(f"\n{'='*40}")
        logger.info(f"Import complete:")
        logger.info(f"  ✅ Inserted : {inserted}")
        logger.info(f"  ⏭  Skipped  : {skipped}")
        logger.info(f"  ❌ Errors   : {errors}")
        logger.info(f"{'='*40}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk import students from CSV")
    parser.add_argument("--file", required=True, help="Path to CSV file")
    args = parser.parse_args()
    run_import(args.file)
