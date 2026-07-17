"""
Alerts route — manage email alerts for at-risk students.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required
from app import db
from app.models.student import Student, PredictionLog
from app.services.ml_service import ml_service
from app.services.email_service import EmailAlertService

alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')
email_service = EmailAlertService()


@alerts_bp.route('/')
@login_required
def dashboard():
    at_risk = _get_at_risk_students()
    alert_logs = PredictionLog.query.filter_by(result='FAIL').order_by(PredictionLog.predicted_at.desc()).limit(50).all()

    return render_template(
        'alerts/dashboard.html',
        at_risk_students=at_risk,
        total_at_risk=len(at_risk),
        alert_logs=alert_logs,
        email_configured=email_service.is_configured,
    )


@alerts_bp.route('/send/<int:student_id>', methods=['POST'])
@login_required
def send_alert(student_id):
    student = Student.query.get_or_404(student_id)
    latest_pred = PredictionLog.query.filter_by(student_id=student.id).order_by(PredictionLog.predicted_at.desc()).first()
    if not latest_pred or latest_pred.result != 'FAIL':
        flash('Student is not at-risk or no prediction found.', 'warning')
        return redirect(url_for('alerts.dashboard'))

    prediction = {
        'result': latest_pred.result,
        'pass_probability': latest_pred.pass_probability,
        'fail_probability': latest_pred.fail_probability,
        'model_name': latest_pred.model_name,
    }

    result = email_service.send_alert(student, prediction)
    if result.get('sent'):
        flash(f'✅ Alert sent for {student.name}!', 'success')
    elif result.get('logged'):
        flash(f'📝 Alert logged (email not configured).', 'info')
    else:
        flash(f'❌ {result.get("message", "Failed")}', 'danger')
    return redirect(url_for('alerts.dashboard'))


@alerts_bp.route('/send-all', methods=['POST'])
@login_required
def send_all():
    at_risk = _get_at_risk_students()
    if not at_risk:
        flash('No at-risk students.', 'info')
        return redirect(url_for('alerts.dashboard'))

    alert_data = []
    for s, p in at_risk:
        alert_data.append((s, {
            'result': p.result,
            'pass_probability': p.pass_probability,
            'fail_probability': p.fail_probability,
            'model_name': p.model_name,
        }))

    results = email_service.send_bulk_alerts(alert_data)
    if results['sent']: flash(f'✅ {results["sent"]} alerts sent!', 'success')
    if results['logged']: flash(f'📝 {results["logged"]} alerts logged.', 'info')
    if results['failed']: flash(f'❌ {results["failed"]} failed.', 'danger')
    return redirect(url_for('alerts.dashboard'))


@alerts_bp.route('/api/at-risk')
def api_at_risk():
    at_risk = _get_at_risk_students()
    return jsonify({
        'success': True,
        'total': len(at_risk),
        'students': [{'id': s.id, 'student_id': s.student_id, 'name': s.name} for s, p in at_risk]
    })


def _get_at_risk_students():
    subq = db.session.query(
        PredictionLog.student_id,
        db.func.max(PredictionLog.predicted_at).label('max_date')
    ).group_by(PredictionLog.student_id).subquery()

    fails = db.session.query(PredictionLog).join(
        subq,
        db.and_(PredictionLog.student_id == subq.c.student_id, PredictionLog.predicted_at == subq.c.max_date)
    ).filter(PredictionLog.result == 'FAIL').all()

    results = []
    for p in fails:
        s = Student.query.get(p.student_id)
        if s: results.append((s, p))
    results.sort(key=lambda x: x[1].pass_probability)
    return results
