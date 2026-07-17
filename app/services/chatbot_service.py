"""
Chatbot Service — Complete Menu-Driven Chatbot
Features: Predict Result, Study Plans, Improvement Tips, FAQs, Contact Admin, Student Lookup & more
"""

import re
from datetime import datetime
from app import db
from app.models.student import Student, PredictionLog
from app.services.ml_service import MLService


class ChatbotService:
    def __init__(self):
        self.user_sessions = {}  # Track user conversation state

    # ─── MENU ────────────────────────────────────────────────────────────────
    def get_menu(self):
        """Return the main menu options."""
        return (
            "🤖 **EduPredict Assistant**\n\n"
            "Select an option:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔮  `1`  **Predict Result**\n"
            "📖  `2`  **Explain Prediction**\n"
            "📚  `3`  **Study Plan**\n"
            "📈  `4`  **Improve Attendance**\n"
            "🎯  `5`  **Improve Marks**\n"
            "❓  `6`  **FAQs**\n"
            "📞  `7`  **Contact Admin**\n"
            "👨‍🎓  `8`  **Student Lookup**\n"
            "📊  `9`  **System Stats**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Type a number or ask me anything! 😊"
        )

    # ─── MAIN PROCESSOR ─────────────────────────────────────────────────────
    def process_message(self, message, session_id="default"):
        msg = message.lower().strip()
        if not msg:
            return {"response": self.get_menu(), "type": "menu"}

        # Check if user is in a conversation flow
        if session_id in self.user_sessions:
            state = self.user_sessions[session_id]
            result = self._handle_state(state, msg, session_id)
            if result:
                return result

        # Menu option routing
        if msg in ["1", "1.", "predict", "predict result"]:
            return self._start_predict_flow(session_id)
        elif msg in ["2", "2.", "explain", "explain prediction"]:
            return {"response": self._explain_prediction(), "type": "answer"}
        elif msg in ["3", "3.", "study plan", "study"]:
            return self._start_study_plan_flow(session_id)
        elif msg in ["4", "4.", "improve attendance", "attendance"]:
            return self._start_improve_attendance_flow(session_id)
        elif msg in ["5", "5.", "improve marks", "marks"]:
            return self._start_improve_marks_flow(session_id)
        elif msg in ["6", "6.", "faq", "faqs"]:
            return {"response": self._get_faqs(), "type": "answer"}
        elif msg in ["7", "7.", "contact", "contact admin", "admin help"]:
            return {"response": self._contact_admin(), "type": "answer"}
        elif msg in ["8", "8.", "student lookup", "lookup"]:
            return self._start_student_lookup_flow(session_id)
        elif msg in ["9", "9.", "stats", "statistics", "system stats"]:
            return self._handle_stats_query(msg)
        elif msg in ["menu", "main menu", "back", "home"]:
            if session_id in self.user_sessions:
                del self.user_sessions[session_id]
            return {"response": self.get_menu(), "type": "menu"}
        elif msg in ["hi", "hello", "hey", "namaste"]:
            return {"response": f"👋 Hello! I'm EduPredict Assistant.\n\n{self.get_menu()}", "type": "menu"}

        # Check for student lookup
        student_check = self._check_student_query(msg)
        if student_check:
            return student_check

        # Knowledge base
        kb_response = self._search_knowledge_base(msg)
        if kb_response:
            return {"response": kb_response, "type": "answer"}

        # Stats check
        if any(kw in msg for kw in ["how many", "total", "count", "pass rate"]):
            return self._handle_stats_query(msg)

        return {"response": f"🤔 I didn't understand that. Here's what I can do:\n\n{self.get_menu()}", "type": "menu"}

    # ─── STATE MANAGEMENT ───────────────────────────────────────────────────
    def _start_predict_flow(self, session_id):
        self.user_sessions[session_id] = {
            "step": "predict_collect",
            "data": {}
        }
        return {
            "response": (
                "🔮 **Predict Your Result**\n\n"
                "Please enter your details in this format:\n\n"
                "`Attendance(%), Internal Marks(0-50), Study Hours/Day, Previous Backlogs`\n\n"
                "Example: `75, 38, 5, 1`\n\n"
                "Or type **back** to return to menu."
            ),
            "type": "form"
        }

    def _start_study_plan_flow(self, session_id):
        self.user_sessions[session_id] = {
            "step": "study_plan_collect",
            "data": {}
        }
        return {
            "response": (
                "📚 **Personalized Study Plan**\n\n"
                "Tell me your current status:\n\n"
                "`Attendance(%), Avg Marks(0-100), Study Hours/Day`\n\n"
                "Example: `65, 55, 2`\n\n"
                "Or type **back** to return to menu."
            ),
            "type": "form"
        }

    def _start_improve_attendance_flow(self, session_id):
        self.user_sessions[session_id] = {
            "step": "improve_attendance",
            "data": {}
        }
        return {
            "response": (
                "📈 **Improve Your Attendance**\n\n"
                "What is your current attendance percentage?\n\n"
                "Example: `60`\n\n"
                "Or type **back** to return to menu."
            ),
            "type": "form"
        }

    def _start_improve_marks_flow(self, session_id):
        self.user_sessions[session_id] = {
            "step": "improve_marks_collect",
            "data": {}
        }
        return {
            "response": (
                "🎯 **Improve Your Marks**\n\n"
                "Enter your marks for 5 subjects (comma-separated, 0-100):\n\n"
                "Example: `55, 60, 42, 70, 48`\n\n"
                "Or type **back** to return to menu."
            ),
            "type": "form"
        }

    def _start_student_lookup_flow(self, session_id):
        self.user_sessions[session_id] = {
            "step": "student_lookup",
            "data": {}
        }
        return {
            "response": (
                "🔍 **Student Lookup**\n\n"
                "Enter a Student ID or Name to look up:\n\n"
                "Example: `MCA2024001` or `Aarav`\n\n"
                "Or type **back** to return to menu."
            ),
            "type": "form"
        }

    def _handle_state(self, state, msg, session_id):
        """Handle multi-step conversation flows."""
        if msg == "back" or msg == "menu":
            del self.user_sessions[session_id]
            return {"response": self.get_menu(), "type": "menu"}

        step = state.get("step")

        if step == "predict_collect":
            return self._process_predict_input(msg, session_id)
        elif step == "study_plan_collect":
            return self._process_study_plan_input(msg, session_id)
        elif step == "improve_attendance":
            return self._process_improve_attendance(msg, session_id)
        elif step == "improve_marks_collect":
            return self._process_improve_marks_input(msg, session_id)
        elif step == "student_lookup":
            del self.user_sessions[session_id]
            return self._handle_student_query(msg)

        return None

    # ─── PREDICT FLOW ────────────────────────────────────────────────────────
    def _process_predict_input(self, msg, session_id):
        """Parse student input and run prediction."""
        nums = self._extract_numbers(msg)
        if len(nums) < 4:
            return {
                "response": (
                    "⚠️ Please enter 4 values: Attendance, Internal Marks, Study Hours, Backlogs\n\n"
                    "Example: `75, 38, 5, 1`\n\n"
                    "Or type **back** to return to menu."
                ),
                "type": "form"
            }

        attendance, internal, study_hours, backlogs = nums[0], nums[1], nums[2], nums[3]

        # Validate ranges
        if not (0 <= attendance <= 100):
            return {"response": "⚠️ Attendance must be between 0 and 100.", "type": "error"}
        if not (0 <= internal <= 50):
            return {"response": "⚠️ Internal marks must be between 0 and 50.", "type": "error"}
        if not (0 <= study_hours <= 10):
            return {"response": "⚠️ Study hours must be between 0 and 10.", "type": "error"}
        if not (0 <= backlogs <= 10):
            return {"response": "⚠️ Backlogs must be between 0 and 10.", "type": "error"}

        # Create synthetic feature vector (using average marks from attendance correlation)
        # If no marks provided, estimate from other values
        estimated_avg = min(100, (attendance * 0.4 + internal * 1.2 + study_hours * 5))
        sub_marks = [estimated_avg] * 5

        features = sub_marks + [internal, attendance, study_hours, 7, backlogs, estimated_avg]

        try:
            ml = MLService()
            pred = ml.predict(features)

            result_icon = "✅" if pred["result"] == "PASS" else "❌"
            conf_label = pred.get("confidence_level", "Moderate")
            pass_prob = pred["pass_probability"]

            # Generate suggestions
            suggestions = self._generate_suggestions(attendance, internal, study_hours, backlogs, estimated_avg, pred["result"])

            response = (
                f"🔮 **Prediction Result**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"  {result_icon} **{pred['result']}**\n"
                f"  Confidence: **{conf_label}**\n"
                f"  Pass Probability: **{pass_prob:.1%}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📊 **Your Inputs:**\n"
                f"• Attendance: **{attendance}%**\n"
                f"• Internal Marks: **{internal}/50**\n"
                f"• Study Hours/Day: **{study_hours}h**\n"
                f"• Backlogs: **{backlogs}**\n\n"
                f"💡 **Suggestions:**\n{suggestions}\n\n"
                f"Type **menu** to go back or ask me anything!"
            )

            del self.user_sessions[session_id]
            return {"response": response, "type": "prediction"}

        except Exception as e:
            return {"response": f"⚠️ Prediction error: {str(e)}", "type": "error"}

    # ─── STUDY PLAN FLOW ────────────────────────────────────────────────────
    def _process_study_plan_input(self, msg, session_id):
        nums = self._extract_numbers(msg)
        if len(nums) < 3:
            return {
                "response": "⚠️ Please enter: Attendance, Avg Marks, Study Hours\nExample: `65, 55, 2`",
                "type": "form"
            }

        attendance, avg_marks, study_hours = nums[0], nums[1], nums[2]
        del self.user_sessions[session_id]

        plan = self._generate_study_plan(attendance, avg_marks, study_hours)
        return {"response": plan, "type": "answer"}

    def _generate_study_plan(self, attendance, avg_marks, study_hours):
        response = "📚 **Your Personalized Study Plan**\n\n"

        # Attendance advice
        if attendance < 75:
            response += f"📈 **Attendance ({attendance}%):** ⚠️ Below 75%!\n"
            response += f"   → Attend **{(75 - attendance)} more classes** to reach safe zone.\n"
            response += "   → Set alarm reminders for class timings.\n\n"
        else:
            response += f"📈 **Attendance ({attendance}%):** ✅ Good! Keep it up.\n\n"

        # Marks advice
        if avg_marks < 40:
            response += f"📝 **Avg Marks ({avg_marks}):** 🔴 Critical!\n"
            response += "   → Focus on **basic concepts** first.\n"
            response += "   → Spend **2 hours daily** revising previous topics.\n"
            response += "   → Ask teachers for **extra help sessions**.\n\n"
        elif avg_marks < 60:
            response += f"📝 **Avg Marks ({avg_marks}):** 🟠 Needs Improvement\n"
            response += "   → Focus on **weak subjects** for 1 extra hour.\n"
            response += "   → Solve **previous year papers**.\n"
            response += "   → Form a **study group** with classmates.\n\n"
        elif avg_marks < 80:
            response += f"📝 **Avg Marks ({avg_marks}):** 🟡 Good\n"
            response += "   → Work on **speed and accuracy**.\n"
            response += "   → Attempt **mock tests** regularly.\n\n"
        else:
            response += f"📝 **Avg Marks ({avg_marks}):** 🟢 Excellent!\n"
            response += "   → Help classmates who are struggling.\n"
            response += "   → Aim for **distinction** in all subjects.\n\n"

        # Study hours advice
        recommended = self._get_recommended_study_hours(avg_marks)
        if study_hours < recommended:
            response += f"⏰ **Study Hours ({study_hours}h/day):** ⚠️ Need {recommended}h/day\n"
            response += "   → **Suggested Schedule:**\n"
            response += f"      • Morning: 1h — Theory revision\n"
            response += f"      • Afternoon: {(recommended-1)//2}h — Problem solving\n"
            response += f"      • Evening: {(recommended-1)-(recommended-1)//2}h — Practice & review\n\n"
        else:
            response += f"⏰ **Study Hours ({study_hours}h/day):** ✅ Sufficient!\n\n"

        # Weekly time table
        response += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        response += "📅 **Recommended Weekly Plan:**\n\n"
        response += "| Day | Focus Area |\n"
        response += "|-----|------------|\n"
        response += "| Mon | Theory & Concepts |\n"
        response += "| Tue | Numerical Problems |\n"
        response += "| Wed | Lab/Practical Work |\n"
        response += "| Thu | Previous Year Papers |\n"
        response += "| Fri | Weak Subject Focus |\n"
        response += "| Sat | Revision & Mock Test |\n"
        response += "| Sun | Rest & Light Reading |\n\n"

        response += "💡 **Pro Tip:** Consistency > Intensity. Study **daily** even if for less time.\n\n"
        response += "Type **menu** for main options."

        return response

    # ─── IMPROVE ATTENDANCE FLOW ─────────────────────────────────────────────
    def _process_improve_attendance(self, msg, session_id):
        nums = self._extract_numbers(msg)
        if not nums:
            return {"response": "Please enter your current attendance percentage.\nExample: `60`", "type": "form"}

        current = nums[0]
        del self.user_sessions[session_id]

        needed = max(0, 75 - current)
        response = (
            f"📈 **Attendance Improvement Plan**\n\n"
            f"**Current:** {current}%\n"
            f"**Target:** 75% (safe zone)\n\n"
        )

        if current >= 75:
            response += "✅ **Great!** Your attendance is already above 75%.\nJust maintain it!\n"
        else:
            response += f"⚠️ **You need {needed:.0f}% more attendance** to reach 75%.\n\n"
            response += "**Tips to Improve:**\n"
            response += "1️⃣ **Track your classes** — Use a calendar or app\n"
            response += "2️⃣ **Reach 5 mins early** — Never miss the start\n"
            response += "3️⃣ **Exchange numbers** — Get notes if you must miss\n"
            response += "4️⃣ **Talk to professors** — Show you care\n"
            response += "5️⃣ **Prioritize** — Attend the subjects you struggle with most\n\n"
            if current < 50:
                response += "🔴 **Serious concern!** Speak to your academic advisor immediately.\n"

        response += "\nType **menu** for more options."
        return {"response": response, "type": "answer"}

    # ─── IMPROVE MARKS FLOW ──────────────────────────────────────────────────
    def _process_improve_marks_input(self, msg, session_id):
        nums = self._extract_numbers(msg)
        if len(nums) < 5:
            return {
                "response": "⚠️ Please enter marks for all 5 subjects.\nExample: `55, 60, 42, 70, 48`",
                "type": "form"
            }

        del self.user_sessions[session_id]
        marks = nums[:5]
        avg = sum(marks) / 5
        subjects = ["Subject 1", "Subject 2", "Subject 3", "Subject 4", "Subject 5"]

        response = "🎯 **Subject-wise Improvement Plan**\n\n"
        response += "| Subject | Marks | Status | Recommendation |\n"
        response += "|---------|-------|--------|----------------|\n"

        weak_subjects = []
        for i, m in enumerate(marks):
            if m >= 75:
                status = "🟢 Strong"
                tip = "Maintain consistency"
            elif m >= 50:
                status = "🟡 Average"
                tip = "Practice more problems"
                weak_subjects.append(subjects[i])
            else:
                status = "🔴 Weak"
                tip = "Start from basics"
                weak_subjects.append(subjects[i])

            response += f"| {subjects[i]} | {m}/100 | {status} | {tip} |\n"

        response += f"\n📊 **Average:** {avg:.1f}/100\n\n"

        if weak_subjects:
            response += "⚠️ **Focus Subjects:**\n"
            for sub in weak_subjects:
                response += f"   • **{sub}** — Dedicate extra 30 mins daily\n"
            response += "\n📖 **General Tips:**\n"
            response += "• Review class notes **same day**\n"
            response += "• Teach concepts to a friend (best way to learn)\n"
            response += "• Use YouTube tutorials for difficult topics\n"
            response += "• Attempt **mock tests** every weekend\n"
        else:
            response += "🌟 **Excellent!** All subjects are strong. Aim for 90%+!\n"

        response += "\nType **menu** for more options."
        return {"response": response, "type": "answer"}

    # ─── EXPLAIN PREDICTION ──────────────────────────────────────────────────
    def _explain_prediction(self):
        return (
            "📖 **How Predictions Work**\n\n"
            "🔮 The system uses **Machine Learning** to predict pass/fail.\n\n"
            "**Key Factors Used (11 features):**\n"
            "📊 **Academic:** Subject marks (5 subjects), Internal marks, Average\n"
            "👤 **Behavioral:** Attendance %, Study hours/day, Assignments, Backlogs\n\n"
            "**How it works:**\n"
            "1️⃣ Your data is fed into a trained ML model\n"
            "2️⃣ The model compares your pattern with 2000+ student records\n"
            "3️⃣ It calculates a **probability score** (0% to 100%)\n"
            "4️⃣ If probability > 50% → **PASS** ✅, else → **FAIL** ❌\n\n"
            "**Confidence Levels:**\n"
            "• 🔵 **Very High** (>90%) — Model is very sure\n"
            "• 🟢 **High** (75-90%) — Model is fairly confident\n"
            "• 🟡 **Moderate** (60-75%) — Borderline prediction\n"
            "• 🔴 **Low** (<60%) — Model is uncertain\n\n"
            "**Best Model:** Logistic Regression (78.3% accuracy, 0.86 ROC-AUC)\n\n"
            "Type **1** to try a prediction yourself!"
        )

    # ─── FAQS ────────────────────────────────────────────────────────────────
    def _get_faqs(self):
        return (
            "❓ **Frequently Asked Questions**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**Q1: How accurate is the prediction?**\n"
            "→ The model is ~78% accurate. We compare 4 ML models and use the best one.\n\n"
            "**Q2: What data is used for prediction?**\n"
            "→ 5 subject marks, internal marks, attendance, study hours, assignments, and backlogs.\n\n"
            "**Q3: Can students see their own prediction?**\n"
            "→ Yes! The Student Portal (at /student/login) lets students view their data.\n\n"
            "**Q4: Is my data safe?**\n"
            "→ Yes. Passwords are hashed, sessions are encrypted, and CSRF is enabled.\n\n"
            "**Q5: What if I forget my password?**\n"
            "→ Admin can reset it from the Student Portal management page.\n\n"
            "**Q6: Can I import many students at once?**\n"
            "→ Yes! Use the Bulk Upload feature (CSV file upload via web UI).\n\n"
            "**Q7: How many students can the system handle?**\n"
            "→ MySQL can handle millions of records. The system is scalable.\n\n"
            "**Q8: Can I get alerts for failing students?**\n"
            "→ Yes! The Email Alerts feature sends notifications for at-risk students.\n\n"
            "**Q9: What ML algorithms are compared?**\n"
            "→ Logistic Regression, Random Forest, Gradient Boosting, and SVM.\n\n"
            "**Q10: Can this work without internet?**\n"
            "→ Yes! It runs locally on your machine with XAMPP.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Type **menu** for main options."
        )

    # ─── CONTACT ADMIN ───────────────────────────────────────────────────────
    def _contact_admin(self):
        return (
            "📞 **Contact Admin**\n\n"
            "Need help? Here's how to reach the administrator:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👤 **Admin Login Page:**\n"
            "   http://localhost:5000/login\n\n"
            "📧 **Email:**\n"
            "   admin@college.edu\n\n"
            "📍 **Location:**\n"
            "   Department of Computer Science\n\n"
            "💬 **Chat Support:**\n"
            "   Available during college hours (9 AM - 5 PM)\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**Common Issues & Solutions:**\n\n"
            "🔐 **Can't login?**\n"
            "   → Default credentials: `admin` / `Admin@1234`\n\n"
            "🔄 **Model not working?**\n"
            "   → Run `python ml/train.py` from terminal\n\n"
            "🗄️ **Database issues?**\n"
            "   → Make sure XAMPP MySQL is running\n\n"
            "📁 **Import errors?**\n"
            "   → Use `.csv` format with the correct column headers\n\n"
            "Type **menu** to return."
        )

    # ─── HELPERS ─────────────────────────────────────────────────────────────
    def _extract_numbers(self, text):
        """Extract all numbers from text."""
        return [float(n) for n in re.findall(r'\d+\.?\d*', text)]

    def _generate_suggestions(self, attendance, internal, study_hours, backlogs, avg_marks, result):
        suggestions = []

        if attendance < 75:
            suggestions.append(f"📈 **Attendance** is {attendance}% — below 75%. Aim to attend **{75 - attendance:.0f}% more classes**.")
        else:
            suggestions.append(f"📈 **Attendance** is {attendance}% — good! Maintain this.")

        if study_hours < 4:
            suggestions.append(f"⏰ **Study** only {study_hours}h/day. Increase to **4-5 hours** for better results.")
        else:
            suggestions.append(f"⏰ **Study** {study_hours}h/day — good habit!")

        if internal < 30:
            suggestions.append(f"📝 **Internal marks** ({internal}/50) need improvement. Submit assignments on time and participate in class.")
        else:
            suggestions.append(f"📝 **Internal marks** ({internal}/50) are decent.")

        if backlogs > 2:
            suggestions.append(f"⚠️ **{backlogs} backlogs** is high. Clear at least 1-2 this semester.")
        elif backlogs > 0:
            suggestions.append(f"⚠️ You have {backlogs} backlog(s). Focus on clearing them.")
        else:
            suggestions.append(f"✅ **No backlogs** — great! Keep it up.")

        if result == "FAIL":
            suggestions.append(f"🔴 **You're at risk!** Please speak to your academic advisor immediately.")
            suggestions.append(f"💪 **Don't lose hope** — start with small daily goals.")

        return "\n".join(f"   {s}" for s in suggestions)

    def _get_recommended_study_hours(self, avg_marks):
        """Recommend study hours based on current average."""
        if avg_marks < 40:
            return 6
        elif avg_marks < 60:
            return 5
        elif avg_marks < 75:
            return 4
        else:
            return 3

    # ─── STUDENT LOOKUP ──────────────────────────────────────────────────────
    def _check_student_query(self, msg):
        """Quick student check from any message."""
        sid_match = re.search(r'(MCA\d+|BCA\d+|CS\d+|IT\d+|EC\d+)', msg, re.IGNORECASE)
        if sid_match:
            sid = sid_match.group(1).upper()
            student = Student.query.filter_by(student_id=sid).first()
            if student:
                return self._format_student(student, detailed=True)
        return None

    def _handle_student_query(self, msg):
        """Handle student lookup from the menu flow."""
        # Check by student ID
        sid_match = re.search(r'(MCA\d+|BCA\d+|CS\d+|IT\d+|EC\d+)', msg, re.IGNORECASE)
        if sid_match:
            sid = sid_match.group(1).upper()
            student = Student.query.filter_by(student_id=sid).first()
            if student:
                return self._format_student(student, detailed=True)
            return {"response": f"❌ No student found with ID **{sid}**\n\nTry a different ID or type **menu**.", "type": "error"}

        # Search by name
        name = msg.strip()
        if len(name) >= 2:
            students = Student.query.filter(Student.name.ilike(f'%{name}%')).limit(5).all()
            if len(students) == 1:
                return self._format_student(students[0], detailed=True)
            elif students:
                response = f"🔍 Found {len(students)} matching students:\n\n"
                for s in students:
                    response += f"• **{s.name}** (`{s.student_id}`) — {s.department}\n"
                response += "\nType a full Student ID to see details."
                return {"response": response, "type": "answer"}

        return {"response": "❌ No student found.\n\nTry a Student ID like `MCA2024001` or type **menu**.", "type": "error"}

    def _format_student(self, student, detailed=False):
        avg = round((student.subject1_marks + student.subject2_marks + student.subject3_marks +
                     student.subject4_marks + student.subject5_marks) / 5.0, 1)

        pred = PredictionLog.query.filter_by(student_id=student.id).order_by(PredictionLog.predicted_at.desc()).first()
        history = PredictionLog.query.filter_by(student_id=student.id).order_by(PredictionLog.predicted_at.desc()).limit(5).all()

        response = (
            f"👨‍🎓 **{student.name}**\n"
            f"`{student.student_id}` | {student.department} | Sem {student.semester}\n\n"
            f"📊 **Academic Profile:**\n"
            f"• 📚 Avg Marks: **{avg}/100**\n"
            f"• 📝 Internal: **{student.internal_marks}/50**\n"
            f"• 📈 Attendance: **{student.attendance_pct}%**\n"
            f"• ⏰ Study: **{student.study_hours_per_day}h/day**\n"
            f"• 📋 Assignments: **{student.assignments_submitted}/10**\n"
            f"• ⚠️ Backlogs: **{student.previous_backlogs}**\n"
        )

        if pred:
            icon = "✅" if pred.result == "PASS" else "❌"
            response += (
                f"\n🔮 **Latest Prediction:** {icon} **{pred.result}**\n"
                f"   Pass Probability: **{pred.pass_probability:.1%}**\n"
                f"   Model: {pred.model_name} | {pred.predicted_at.strftime('%d %b %Y')}\n"
            )

        if detailed and history:
            response += "\n📜 **Prediction History:**\n"
            for i, p in enumerate(history[:5], 1):
                ico = "✅" if p.result == "PASS" else "❌"
                response += f"{i}. {ico} {p.result} ({p.pass_probability:.1%}) — {p.predicted_at.strftime('%d %b')}\n"

        response += "\n💡 **Tip:** Use option **3** for a study plan!\n" if detailed else ""
        response += "\nType **menu** for main options."

        return {"response": response, "type": "student_data"}

    # ─── STATISTICS ──────────────────────────────────────────────────────────
    def _handle_stats_query(self, msg):
        total = Student.query.count()
        predictions = PredictionLog.query.count()
        passes = PredictionLog.query.filter_by(result='PASS').count()
        fails = PredictionLog.query.filter_by(result='FAIL').count()
        rate = round((passes / max(predictions, 1)) * 100, 1)

        return {
            "response": (
                f"📊 **System Statistics**\n\n"
                f"👥 **Total Students:** {total}\n"
                f"🔮 **Total Predictions:** {predictions}\n"
                f"✅ **PASS:** {passes} ({rate}%)\n"
                f"❌ **FAIL:** {fails} ({100-rate}%)\n\n"
                f"Type **menu** for main options."
            ),
            "type": "stats"
        }

    # ─── KNOWLEDGE BASE ─────────────────────────────────────────────────────
    def _search_knowledge_base(self, msg):
        """Fallback knowledge base for general questions."""
        kb = {
            "project": ["what is this", "about project", "tell me about"],
            "tech": ["tech stack", "technology", "framework", "tools"],
            "ml": ["machine learning", "model", "algorithm", "classifier", "logistic", "random forest", "svm"],
            "features": ["features", "input", "data used", "parameters"],
            "accuracy": ["accuracy", "how accurate", "performance", "precision", "recall", "roc"],
            "confusion": ["confusion matrix", "tp", "tn", "fp", "fn"],
            "scaler": ["standard scaler", "scaling", "normalization"],
            "architecture": ["mvc", "architecture", "structure", "pattern"],
            "setup": ["how to run", "setup", "installation", "deploy", "install"],
            "viva": ["viva", "question", "interview", "exam"],
            "login": ["login", "credentials", "password", "sign in"],
        }

        responses = {
            "project": "🎓 **Student Pass/Fail Prediction System**\n\nAn MCA project using ML to predict if students will pass or fail based on academics & behavior.",
            "tech": "🛠️ **Stack:** Flask + MySQL + scikit-learn + Bootstrap 5 + Chart.js",
            "ml": "🤖 **4 Models:** Logistic Regression, Random Forest, Gradient Boosting, SVM. Best selected by ROC-AUC.",
            "features": "📊 **11 Features:** 5 subject marks, internal marks, attendance, study hours, assignments, backlogs, average.",
            "accuracy": "📈 **Accuracy:** ~78% | ROC-AUC: 0.86 | Best model: Logistic Regression",
            "confusion": "📊 **CM:** TN=149, FP=38, FN=49, TP=164 for best model.",
            "scaler": "📐 **StandardScaler:** Normalizes features so larger ranges don't dominate.",
            "architecture": "🏗️ **MVC:** Models (data) → Controllers (routes) → Views (templates) + Services layer.",
            "setup": "🚀 `pip install -r requirements.txt` → `python ml/train.py` → `python run.py` → http://localhost:5000",
            "viva": "❓ **Viva Q&A available!** Type `6` for FAQs or ask specific questions.",
            "login": "🔐 **Admin:** `admin` / `Admin@1234` | **Student Portal:** /student/login",
        }

        for topic, keywords in kb.items():
            if any(k in msg for k in keywords):
                return responses.get(topic)

        return None
