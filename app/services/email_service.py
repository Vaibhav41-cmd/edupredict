"""
Email Alert Service — sends email notifications for at-risk students.
Fails gracefully when email is not configured.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import current_app, render_template

logger = logging.getLogger(__name__)


class EmailAlertService:
    def __init__(self):
        self._loaded = False
        self._enabled = False
        self._smtp_host = None
        self._smtp_port = None
        self._smtp_user = None
        self._smtp_pass = None
        self._from_email = None
        self._admin_email = None

    def _load_config(self):
        try:
            cfg = current_app.config
            self._smtp_host = cfg.get('SMTP_HOST', '')
            self._smtp_port = cfg.get('SMTP_PORT', 587)
            self._smtp_user = cfg.get('SMTP_USER', '')
            self._smtp_pass = cfg.get('SMTP_PASS', '')
            self._from_email = cfg.get('FROM_EMAIL', '')
            self._admin_email = cfg.get('ADMIN_EMAIL', '')
            self._enabled = all([self._smtp_host, self._smtp_user, self._smtp_pass, self._from_email])
            self._loaded = True
        except (RuntimeError, KeyError):
            self._enabled = False
            self._loaded = True

    @property
    def is_configured(self):
        if not self._loaded:
            self._load_config()
        return self._enabled

    def send_alert(self, student, prediction, recipient_email=None):
        if not self._loaded:
            self._load_config()

        to_email = recipient_email or self._admin_email
        if not to_email:
            return {'sent': False, 'message': 'No recipient email configured'}

        if not self._enabled:
            logger.warning(
                f'[EMAIL DISABLED] ALERT: {student.student_id} ({student.name}) '
                f'predicted {prediction["result"]} — logged instead of sent'
            )
            return {'sent': False, 'message': 'Email not configured. Alert logged.', 'logged': True}

        try:
            avg_marks = round((
                student.subject1_marks + student.subject2_marks +
                student.subject3_marks + student.subject4_marks + student.subject5_marks
            ) / 5.0, 1)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'⚠️ AT-RISK: {student.student_id} — {student.name} Predicted FAIL'
            msg['From'] = self._from_email
            msg['To'] = to_email

            html = f"""
            <html><body style="font-family:sans-serif;padding:20px;">
            <div style="max-width:600px;margin:auto;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #ddd;">
            <div style="background:#dc3545;color:#fff;padding:20px;text-align:center;">
            <h2 style="margin:0;">⚠️ At-Risk Student Alert</h2></div>
            <div style="padding:20px;">
            <p><strong>{student.name}</strong> (<code>{student.student_id}</code>)</p>
            <table style="width:100%;border-collapse:collapse;">
            <tr><td style="padding:6px 0;color:#666;">Department</td><td style="font-weight:600;">{student.department}</td></tr>
            <tr><td style="padding:6px 0;color:#666;">Semester</td><td style="font-weight:600;">{student.semester}</td></tr>
            <tr><td style="padding:6px 0;color:#666;">Avg Marks</td><td style="font-weight:600;">{avg_marks}/100</td></tr>
            <tr><td style="padding:6px 0;color:#666;">Attendance</td><td style="font-weight:600;">{student.attendance_pct}%</td></tr>
            <tr><td style="padding:6px 0;color:#666;">Backlogs</td><td style="font-weight:600;">{student.previous_backlogs}</td></tr>
            </table>
            <div style="text-align:center;margin:20px 0;padding:15px;background:#fef2f2;border-radius:8px;">
            <span style="font-size:1.2rem;font-weight:700;color:#dc3545;">❌ PREDICTED: FAIL</span>
            <p style="margin:8px 0;">Pass Probability: <strong>{prediction['pass_probability']:.1%}</strong></p>
            </div>
            <p><strong>Suggested Actions:</strong></p>
            <ul><li>Schedule a meeting with the student</li><li>Review attendance and performance</li><li>Consider peer tutoring</li></ul>
            </div></div></body></html>
            """
            msg.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.starttls()
                server.login(self._smtp_user, self._smtp_pass)
                server.send_message(msg)

            logger.info(f'Alert sent for {student.student_id} to {to_email}')
            return {'sent': True, 'message': f'Alert sent to {to_email}'}

        except Exception as e:
            logger.error(f'Email error: {e}')
            return {'sent': False, 'message': f'Error: {str(e)}'}

    def send_bulk_alerts(self, at_risk_students):
        results = {'sent': 0, 'failed': 0, 'logged': 0}
        for student, prediction in at_risk_students:
            r = self.send_alert(student, prediction)
            if r.get('sent'): results['sent'] += 1
            elif r.get('logged'): results['logged'] += 1
            else: results['failed'] += 1
        return results
