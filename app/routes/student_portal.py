"""
Student Portal — separate login for students to view their own data.
"""

import functools
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash
from app import db
from app.models.student import Student, PredictionLog
from app.models.student_auth import StudentAuth

student_portal_bp = Blueprint('student_portal', __name__, url_prefix='/student')


def student_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'student_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('student_portal.login'))
        return f(*args, **kwargs)
    return decorated


@student_portal_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'student_id' in session:
        return redirect(url_for('student_portal.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        auth = StudentAuth.query.filter_by(username=username).first()

        if auth and auth.check_password(password) and auth.is_active:
            session['student_id'] = auth.student_id
            session['student_username'] = auth.username
            auth.last_login = datetime.utcnow()
            db.session.commit()
            flash(f'Welcome, {auth.student.name}!', 'success')
            return redirect(url_for('student_portal.dashboard'))

        flash('Invalid username or password.', 'danger')

    return render_template('student_portal/login.html')


@student_portal_bp.route('/logout')
def logout():
    session.pop('student_id', None)
    session.pop('student_username', None)
    flash('Logged out.', 'info')
    return redirect(url_for('student_portal.login'))


@student_portal_bp.route('/dashboard')
@student_required
def dashboard():
    student = Student.query.get_or_404(session['student_id'])
    latest_pred = PredictionLog.query.filter_by(student_id=student.id).order_by(PredictionLog.predicted_at.desc()).first()
    history = PredictionLog.query.filter_by(student_id=student.id).order_by(PredictionLog.predicted_at.desc()).limit(10).all()
    avg = round((student.subject1_marks + student.subject2_marks + student.subject3_marks +
                 student.subject4_marks + student.subject5_marks) / 5.0, 1)

    return render_template('student_portal/dashboard.html', student=student, latest_pred=latest_pred,
                           prediction_history=history, avg_marks=avg)


@student_portal_bp.route('/change-password', methods=['GET', 'POST'])
@student_required
def change_password():
    student = Student.query.get(session['student_id'])
    auth = StudentAuth.query.filter_by(student_id=student.id).first()

    if request.method == 'POST':
        if not auth.check_password(request.form.get('current_password', '')):
            flash('Current password is incorrect.', 'danger')
        elif len(request.form.get('new_password', '')) < 6:
            flash('New password must be at least 6 characters.', 'danger')
        elif request.form.get('new_password') != request.form.get('confirm_password'):
            flash('Passwords do not match.', 'danger')
        else:
            auth.set_password(request.form.get('new_password'))
            db.session.commit()
            flash('✅ Password changed!', 'success')
            return redirect(url_for('student_portal.dashboard'))

    return render_template('student_portal/change_password.html', student=student)


@student_portal_bp.route('/admin/manage', methods=['GET', 'POST'])
def admin_manage():
    from flask_login import current_user
    if not current_user.is_authenticated:
        flash('Admin login required.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        sid = request.form.get('student_id_db', '').strip()
        action = request.form.get('action', '')
        student = Student.query.get(int(sid)) if sid.isdigit() else None

        if action == 'create' and student:
            if StudentAuth.query.filter_by(student_id=student.id).first():
                flash(f'Account already exists for {student.name}.', 'warning')
            else:
                auth = StudentAuth(student_id=student.id, username=student.student_id, is_active=True)
                auth.set_password(student.student_id)
                db.session.add(auth)
                db.session.commit()
                flash(f'✅ Account created! Password: {student.student_id}', 'success')

        elif action == 'reset':
            auth = StudentAuth.query.filter_by(student_id=int(sid)).first()
            if auth and student:
                auth.set_password(student.student_id)
                db.session.commit()
                flash(f'✅ Password reset to: {student.student_id}', 'success')

        elif action == 'toggle':
            auth = StudentAuth.query.filter_by(student_id=int(sid)).first()
            if auth:
                auth.is_active = not auth.is_active
                db.session.commit()
                flash(f'Account {"activated" if auth.is_active else "deactivated"}.', 'success')

    accounts = StudentAuth.query.order_by(StudentAuth.created_at.desc()).all()
    existing_ids = [a.student_id for a in accounts]
    students_without = Student.query.filter(~Student.id.in_(existing_ids)).limit(20).all() if existing_ids else Student.query.limit(20).all()

    return render_template('student_portal/admin_manage.html', accounts=accounts, students_without=students_without)
