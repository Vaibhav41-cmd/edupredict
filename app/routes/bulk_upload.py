"""
Bulk Upload route — upload student data via CSV through the web UI.
"""

import csv
import io
import json
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, make_response
from flask_login import login_required
from werkzeug.security import generate_password_hash
from app import db
from app.models.student import Student, PredictionLog
from app.services.ml_service import ml_service

bulk_bp = Blueprint('bulk', __name__, url_prefix='/bulk')

VALID_DEPARTMENTS = {'MCA', 'BCA', 'CS', 'IT', 'EC', 'EE', 'ME', 'CE'}

REQUIRED_COLUMNS = [
    'name', 'email', 'department', 'semester',
    'subject1_marks', 'subject2_marks', 'subject3_marks',
    'subject4_marks', 'subject5_marks', 'internal_marks',
    'attendance_pct', 'study_hours_per_day',
    'assignments_submitted', 'previous_backlogs',
]


@bulk_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file selected.', 'danger')
            return render_template('bulk/upload.html')

        file = request.files['csv_file']
        if file.filename == '' or not file.filename.endswith('.csv'):
            flash('Please select a valid .csv file.', 'danger')
            return render_template('bulk/upload.html')

        result = _process_csv(file)
        if result['inserted'] > 0:
            flash(f'✅ Imported {result["inserted"]} students with predictions!', 'success')
        if result['skipped'] > 0:
            flash(f'⏭️ Skipped {result["skipped"]} duplicates.', 'warning')
        if result['errors'] > 0:
            flash(f'❌ {result["errors"]} errors. See details below.', 'danger')

        return render_template('bulk/upload.html', result=result, show_result=True)

    return render_template('bulk/upload.html', show_result=False)


@bulk_bp.route('/template')
@login_required
def download_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(REQUIRED_COLUMNS + ['student_id'])
    writer.writerow(['Aarav Sharma', 'aarav@college.edu', 'MCA', 3, 85, 78, 92, 88, 76, 42, 92.5, 6.5, 9, 0, 'MCA2024099'])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=student_upload_template.csv'
    return response


def _process_csv(file):
    result = {'total': 0, 'inserted': 0, 'skipped': 0, 'errors': 0, 'error_details': [], 'inserted_details': []}

    try:
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        columns = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLUMNS if c not in columns]
        if missing:
            result['errors'] = 1
            result['error_details'].append(f'Missing columns: {", ".join(missing)}')
            return result

        ml_ready = ml_service.is_ready()
        row_num = 0

        for row in reader:
            row_num += 1
            result['total'] = row_num
            try:
                cleaned = {k: (v or '').strip() for k, v in row.items()}
                sid = cleaned.get('student_id', '').strip() or f'BULK{datetime.now().strftime("%y%m%d")}{row_num:04d}'

                if Student.query.filter_by(student_id=sid).first():
                    result['skipped'] += 1
                    continue

                student = Student(
                    student_id=sid, name=cleaned['name'], email=cleaned['email'],
                    department=cleaned['department'], semester=int(float(cleaned['semester'])),
                    subject1_marks=int(float(cleaned['subject1_marks'])),
                    subject2_marks=int(float(cleaned['subject2_marks'])),
                    subject3_marks=int(float(cleaned['subject3_marks'])),
                    subject4_marks=int(float(cleaned['subject4_marks'])),
                    subject5_marks=int(float(cleaned['subject5_marks'])),
                    internal_marks=int(float(cleaned['internal_marks'])),
                    attendance_pct=float(cleaned['attendance_pct']),
                    study_hours_per_day=float(cleaned['study_hours_per_day']),
                    assignments_submitted=int(float(cleaned['assignments_submitted'])),
                    previous_backlogs=int(float(cleaned['previous_backlogs'])),
                )
                db.session.add(student)
                db.session.flush()

                if ml_ready:
                    features = student.feature_vector()
                    pred = ml_service.predict(features)
                    log = PredictionLog(
                        student_id=student.id, result=pred['result'],
                        pass_probability=pred['pass_probability'],
                        fail_probability=pred['fail_probability'],
                        model_name=pred['model_name'], model_version=pred.get('model_version', '1.0'),
                        feature_snapshot=json.dumps(features),
                    )
                    db.session.add(log)

                result['inserted'] += 1
                result['inserted_details'].append({'student_id': sid, 'name': cleaned['name']})

                if result['inserted'] % 50 == 0:
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                result['errors'] += 1
                result['error_details'].append(f'Row {row_num}: {str(e)}')

        db.session.commit()
    except Exception as e:
        result['errors'] += 1
        result['error_details'].append(f'File error: {str(e)}')

    return result
