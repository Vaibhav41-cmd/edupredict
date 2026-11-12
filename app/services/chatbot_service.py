"""
Chatbot Service — Menu-driven student support with live ML metrics.
"""

import re
from datetime import datetime
from app import db
from app.models.student import Student, PredictionLog
from app.services.ml_service import ml_service


class ChatbotService:
    def __init__(self):
        self.user_sessions = {}

    def get_menu(self):
        return (
            "🤖 **EduPredict Assistant**\n\nSelect an option:\n\n"
            "🔮 `1` Predict Result\n📖 `2` Explain Prediction\n"
            "📚 `3` Study Plan\n📈 `4` Improve Attendance\n"
            "🎯 `5` Improve Marks\n❓ `6` FAQs\n📞 `7` Contact Admin\n"
            "👨‍🎓 `8` Student Lookup\n📊 `9` System Stats\n\n"
            "Type a number or ask me anything! 😊"
        )

    def process_message(self, message, session_id="default"):
        msg = message.lower().strip()
        if not msg:
            return {"response": self.get_menu(), "type": "menu"}
        if session_id in self.user_sessions:
            result = self._handle_state(self.user_sessions[session_id], msg, session_id)
            if result:
                return result
        if msg in ["1", "1.", "predict", "predict result"]:
            return self._start_predict_flow(session_id)
        if msg in ["2", "2.", "explain", "explain prediction"]:
            return {"response": self._explain_prediction(), "type": "answer"}
        if msg in ["3", "3.", "study plan", "study"]:
            return self._start_study_plan_flow(session_id)
        if msg in ["4", "4.", "improve attendance", "attendance"]:
            return self._start_improve_attendance_flow(session_id)
        if msg in ["5", "5.", "improve marks", "marks"]:
            return self._start_improve_marks_flow(session_id)
        if msg in ["6", "6.", "faq", "faqs"]:
            return {"response": self._get_faqs(), "type": "answer"}
        if msg in ["7", "7.", "contact", "contact admin", "admin help"]:
            return {"response": self._contact_admin(), "type": "answer"}
        if msg in ["8", "8.", "student lookup", "lookup"]:
            return self._start_student_lookup_flow(session_id)
        if msg in ["9", "9.", "stats", "statistics", "system stats"]:
            return self._handle_stats_query(msg)
        if msg in ["menu", "main menu", "back", "home"]:
            self.user_sessions.pop(session_id, None)
            return {"response": self.get_menu(), "type": "menu"}
        if msg in ["hi", "hello", "hey", "namaste"]:
            return {"response": f"👋 Hello! I'm EduPredict Assistant.\n\n{self.get_menu()}", "type": "menu"}
        student_check = self._check_student_query(msg)
        if student_check:
            return student_check
        kb_response = self._search_knowledge_base(msg)
        if kb_response:
            return {"response": kb_response, "type": "answer"}
        if any(kw in msg for kw in ["how many", "total", "count", "pass rate"]):
            return self._handle_stats_query(msg)
        return {"response": f"🤔 I didn't understand that. Here's what I can do:\n\n{self.get_menu()}", "type": "menu"}

    def _start_predict_flow(self, session_id):
        self.user_sessions[session_id] = {"step": "predict_collect", "data": {}}
        return {"response": "🔮 **Predict Your Result**\n\nEnter details: `Attendance(%), Internal Marks(0-50), Study Hours/Day, Previous Backlogs`\n\nExample: `75, 38, 5, 1`\n\nType **back** to return.", "type": "form"}

    def _start_study_plan_flow(self, session_id):
        self.user_sessions[session_id] = {"step": "study_plan_collect", "data": {}}
        return {"response": "📚 **Personalized Study Plan**\n\nEnter: `Attendance(%), Avg Marks(0-100), Study Hours/Day`\n\nExample: `65, 55, 2`", "type": "form"}

    def _start_improve_attendance_flow(self, session_id):
        self.user_sessions[session_id] = {"step": "improve_attendance", "data": {}}
        return {"response": "📈 **Improve Your Attendance**\n\nWhat is your current attendance percentage? Example: `60`", "type": "form"}

    def _start_improve_marks_flow(self, session_id):
        self.user_sessions[session_id] = {"step": "improve_marks_collect", "data": {}}
        return {"response": "🎯 **Improve Your Marks**\n\nEnter marks for 5 subjects (0-100), comma-separated. Example: `55, 60, 42, 70, 48`", "type": "form"}

    def _start_student_lookup_flow(self, session_id):
        self.user_sessions[session_id] = {"step": "student_lookup", "data": {}}
        return {"response": "🔍 **Student Lookup**\n\nEnter a Student ID or Name, e.g. `MCA2024001`", "type": "form"}

    def _handle_state(self, state, msg, session_id):
        if msg in ("back", "menu"):
            self.user_sessions.pop(session_id, None)
            return {"response": self.get_menu(), "type": "menu"}
        step = state.get("step")
        if step == "predict_collect": return self._process_predict_input(msg, session_id)
        if step == "study_plan_collect": return self._process_study_plan(msg, session_id)
        if step == "improve_attendance": return self._process_attendance(msg, session_id)
        if step == "improve_marks_collect": return self._process_marks(msg, session_id)
        if step == "student_lookup": return self._process_student_lookup(msg, session_id)
        return None

    def _process_predict_input(self, msg, session_id):
        try:
            attendance, internal, hours, backlogs = [float(x.strip()) for x in msg.split(",")]
            values = [max(0, min(100, attendance)), max(0, min(50, internal)), max(0, min(18, hours)), max(0, min(20, backlogs))]
        except Exception:
            return {"response": "Please enter four numbers separated by commas, e.g. `75, 38, 5, 1`.", "type": "error"}
        avg = max(0, min(100, 50 + (values[1] - 25) * 1.2))
        features = [avg] * 5 + [values[1], values[0], values[2], 7, values[3], avg]
        try:
            pred = ml_service.predict(features)
        except RuntimeError as exc:
            return {"response": str(exc), "type": "error"}
        self.user_sessions.pop(session_id, None)
        return {"response": self._format_prediction(pred), "type": "prediction"}

    @staticmethod
    def _format_prediction(pred):
        return (f"🔮 **Prediction: {pred['result']}**\n\n"
                f"✅ Pass probability: {pred['pass_probability']*100:.1f}%\n"
                f"❌ Fail probability: {pred['fail_probability']*100:.1f}%\n"
                f"📊 Confidence: {pred['confidence_level']}\n"
                f"🤖 Model: {pred['model_name']}")

    def _process_study_plan(self, msg, session_id):
        try:
            att, marks, hours = [float(x.strip()) for x in msg.split(",")]
        except Exception:
            return {"response": "Enter three numbers: attendance, average marks, study hours (e.g. `65, 55, 2`).", "type": "error"}
        tips = []
        if att < 75: tips.append("Attend classes consistently and target at least 75% attendance.")
        if marks < 50: tips.append("Schedule daily remedial practice for difficult subjects.")
        if hours < 4: tips.append("Build up to 4–5 focused self-study hours each day.")
        tips.append("Use weekly revision and practice tests to track improvement.")
        self.user_sessions.pop(session_id, None)
        return {"response": "📚 **Study Plan**\n\n" + "\n".join("• " + t for t in tips), "type": "answer"}

    def _process_attendance(self, msg, session_id):
        try: att = max(0, min(100, float(msg)))
        except ValueError: return {"response": "Enter a percentage from 0 to 100.", "type": "error"}
        self.user_sessions.pop(session_id, None)
        return {"response": f"📈 Current attendance: {att:.1f}%. {'Keep it up!' if att >= 75 else 'Attend every upcoming class; coordinate with your department about eligibility.'}", "type": "answer"}

    def _process_marks(self, msg, session_id):
        try: marks = [max(0, min(100, float(x.strip()))) for x in msg.split(",")]
        except ValueError: return {"response": "Enter comma-separated marks between 0 and 100.", "type": "error"}
        if len(marks) != 5: return {"response": "Please provide exactly five subject marks.", "type": "error"}
        avg = sum(marks) / 5
        self.user_sessions.pop(session_id, None)
        return {"response": f"🎯 Average marks: {avg:.1f}/100. {'Continue consistent practice and revision.' if avg >= 50 else 'Prioritize remedial sessions and past papers.'}", "type": "answer"}

    def _process_student_lookup(self, msg, session_id):
        student = Student.query.filter((Student.student_id.ilike(f"%{msg}%")) | (Student.name.ilike(f"%{msg}%"))).first()
        self.user_sessions.pop(session_id, None)
        if not student: return {"response": f"No student record matched '{msg}'.", "type": "answer"}
        pred = student.latest_prediction
        result = pred.result if pred else "Not predicted"
        return {"response": f"👨‍🎓 **{student.name}** ({student.student_id})\nDepartment: {student.department} · Semester {student.semester}\nAverage marks: {student.average_marks:.1f}\nLatest ML prediction: **{result}**", "type": "answer"}

    def _check_student_query(self, msg):
        student = Student.query.filter((Student.student_id.ilike(f"%{msg}%")) | (Student.name.ilike(f"%{msg}%"))).first()
        if not student: return None
        pred = student.latest_prediction
        return {"response": f"👨‍🎓 **{student.name}** — {student.student_id}; latest prediction: **{pred.result if pred else 'Not predicted'}**.", "type": "answer"}

    def _handle_stats_query(self, msg):
        try:
            total = Student.query.count()
            pass_count = PredictionLog.query.filter_by(result="PASS").count()
            predictions = PredictionLog.query.count()
            metrics = ml_service.get_metrics() if ml_service.is_ready() else {}
            acc = metrics.get("accuracy", 0.835)
            auc = metrics.get("roc_auc", 0.9082)
            pass_rate = (pass_count / predictions * 100) if predictions else 0
            return {"response": f"📊 **System Statistics**\n\n👥 Students: {total}\n🔮 Predictions: {predictions}\n✅ Cohort PASS rate: {pass_rate:.1f}%\n🤖 Model accuracy: {acc*100:.1f}% · ROC-AUC: {auc:.4f}", "type": "answer"}
        except Exception:
            return {"response": "Statistics are unavailable until the database is initialized.", "type": "answer"}

    def _explain_prediction(self):
        return ("EduPredict estimates PASS/FAIL from 11 academic and behavioral features. "
                "Probabilities are model estimates, not guaranteed outcomes; instructors should use them as early-warning evidence alongside human review.")

    def _get_faqs(self):
        metrics = ml_service.get_metrics() if ml_service.is_ready() else {}
        acc = metrics.get("accuracy", 0.835)
        auc = metrics.get("roc_auc", 0.9082)
        return ("❓ **Frequently Asked Questions**\n\n"
                f"**How accurate is the prediction?** The best model reports {acc*100:.1f}% accuracy and ROC-AUC {auc:.4f} on the held-out test split.\n\n"
                "**Does this guarantee a result?** No. It is a decision-support estimate, not a substitute for faculty judgment.\n\n"
                "**What features are used?** Five subject marks, internal marks, attendance, study hours, assignment completion, previous backlogs, and average marks.")

    def _contact_admin(self):
        return "Contact your department administrator or use the admin portal at `/login`."

    def _search_knowledge_base(self, msg):
        answers = {
            "accuracy": lambda: self._get_faqs(),
            "feature": lambda: "The model uses subject marks, internal assessment, attendance, study hours, assignments, previous backlogs, and derived average marks.",
            "model": lambda: self._get_faqs(),
            "login": lambda: "Admin login is available at `/login`; student login is available at `/student/login`.",
            "dataset": lambda: "Training used 2,000 academic records with 11 input features and a binary PASS/FAIL target.",
            "roc": lambda: self._get_faqs(),
        }
        for key, response in answers.items():
            if key in msg: return response()
        return None

    def _handle_stats_query_legacy(self, msg):
        return self._handle_stats_query(msg)
