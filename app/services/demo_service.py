"""
app/services/demo_service.py — Demo Dataset Seeding & Reset Service

Seeds realistic MCA, BCA, Computer Science, and IT student profiles,
runs real ML predictions via MLService, and provisions Student Portal
demo credentials so the application works out-of-the-box without XAMPP.
"""

from datetime import datetime, timedelta
from app import db
from app.models.student import Student, PredictionLog
from app.models.student_auth import StudentAuth
from app.services.ml_service import ml_service

DEMO_STUDENTS = [
    # (student_id, name, email, dept, sem, s1, s2, s3, s4, s5, internal, att, hrs, assign, backlogs)
    ("MCA2024001", "Rahul Sharma",     "rahul.sharma@demo.edu",     "MCA", 3, 78, 82, 75, 88, 71, 42, 88.5, 5.0, 9,  0),
    ("MCA2024002", "Priya Patel",      "priya.patel@demo.edu",      "MCA", 3, 55, 48, 62, 50, 57, 28, 62.0, 2.5, 6,  2),
    ("MCA2024003", "Arjun Mehta",      "arjun.mehta@demo.edu",      "MCA", 3, 90, 87, 93, 88, 85, 48, 95.0, 7.0, 10, 0),
    ("MCA2024004", "Sneha Joshi",      "sneha.joshi@demo.edu",      "MCA", 3, 35, 40, 28, 45, 32, 18, 48.0, 1.5, 3,  4),
    ("MCA2024005", "Vikram Nair",      "vikram.nair@demo.edu",      "MCA", 3, 68, 72, 65, 70, 74, 36, 78.0, 4.0, 7,  1),
    ("BCA2024001", "Ananya Gupta",     "ananya.gupta@demo.edu",     "BCA", 2, 82, 79, 85, 80, 88, 44, 91.0, 6.0, 10, 0),
    ("BCA2024002", "Ravi Kumar",       "ravi.kumar@demo.edu",       "BCA", 2, 42, 38, 44, 40, 36, 20, 55.0, 2.0, 4,  3),
    ("MCA2024006", "Divya Singh",      "divya.singh@demo.edu",      "MCA", 3, 76, 80, 73, 78, 82, 40, 82.0, 5.5, 8,  0),
    ("MCA2024007", "Karan Malhotra",   "karan.malhotra@demo.edu",   "MCA", 3, 28, 32, 35, 30, 25, 14, 42.0, 1.0, 2,  5),
    ("MCA2024008", "Neha Verma",       "neha.verma@demo.edu",       "MCA", 2, 65, 70, 68, 72, 60, 34, 74.0, 3.5, 7,  1),
    ("MCA2024009", "Vaibhav Desale",   "vaibhav.desale@demo.edu",   "MCA", 3, 89, 91, 86, 92, 88, 47, 94.0, 6.5, 10, 0),
    ("MCA2024010", "Rutuja Kulkarni",  "rutuja.kulkarni@demo.edu",  "MCA", 3, 84, 81, 79, 86, 83, 43, 89.5, 5.5, 9,  0),
    ("MCA2024011", "Omkar Deshmukh",   "omkar.deshmukh@demo.edu",   "MCA", 3, 44, 39, 41, 36, 42, 21, 52.5, 1.5, 4,  3),
    ("MCA2024012", "Tejaswini Patil",  "tejaswini.patil@demo.edu",  "MCA", 3, 74, 77, 71, 75, 79, 39, 84.0, 4.5, 8,  0),
    ("MCA2024013", "Sanket Jadhav",    "sanket.jadhav@demo.edu",    "MCA", 1, 61, 64, 58, 63, 60, 31, 71.0, 3.0, 6,  1),
    ("MCA2024014", "Pratiksha Shinde", "pratiksha.shinde@demo.edu", "MCA", 3, 31, 29, 34, 37, 28, 16, 44.0, 1.0, 3,  4),
    ("MCA2024015", "Aditya Pawar",     "aditya.pawar@demo.edu",     "MCA", 4, 80, 76, 84, 79, 81, 41, 86.0, 5.0, 9,  0),
    ("MCA2024016", "Shraddha Chavan",  "shraddha.chavan@demo.edu",  "MCA", 2, 71, 69, 73, 68, 75, 37, 79.5, 4.0, 8,  0),
    ("BCA2024003", "Rohan Gaikwad",    "rohan.gaikwad@demo.edu",    "BCA", 3, 38, 42, 35, 40, 33, 19, 49.0, 1.5, 3,  3),
    ("BCA2024004", "Pooja More",       "pooja.more@demo.edu",       "BCA", 4, 77, 80, 74, 76, 82, 40, 85.0, 4.5, 9,  0),
    ("CS2024001",  "Siddharth Bhosale","siddharth.b@demo.edu",      "Computer Science", 4, 86, 88, 84, 90, 85, 45, 92.0, 6.0, 10, 0),
    ("CS2024002",  "Mayuri Sawant",    "mayuri.sawant@demo.edu",    "Computer Science", 2, 47, 43, 45, 39, 41, 22, 57.0, 2.0, 4,  2),
    ("CS2024003",  "Nikhil Gokhale",   "nikhil.gokhale@demo.edu",   "Computer Science", 3, 69, 73, 70, 66, 72, 35, 77.0, 4.0, 8,  0),
    ("IT2024001",  "Aishwarya Kadam",  "aishwarya.k@demo.edu",      "Information Technology", 3, 81, 78, 83, 80, 79, 42, 87.5, 5.0, 9,  0),
    ("IT2024002",  "Tushar Sonawane",  "tushar.s@demo.edu",         "Information Technology", 1, 33, 36, 29, 35, 31, 15, 45.5, 1.0, 2,  4),
    ("IT2024003",  "Mrunal Thorat",    "mrunal.thorat@demo.edu",    "Information Technology", 2, 64, 67, 62, 69, 65, 33, 76.0, 3.5, 7,  1),
    ("MCA2024017", "Swapnil Bhalerao", "swapnil.b@demo.edu",        "MCA", 3, 43, 40, 38, 44, 37, 20, 54.0, 1.5, 4,  3),
    ("MCA2024018", "Komal Wagh",       "komal.wagh@demo.edu",       "MCA", 3, 87, 85, 90, 84, 89, 46, 93.0, 6.0, 10, 0),
    ("MCA2024019", "Harshal Nikam",    "harshal.nikam@demo.edu",    "MCA", 2, 58, 61, 56, 60, 63, 30, 69.0, 3.0, 6,  1),
    ("MCA2024020", "Gayatri Salunkhe", "gayatri.s@demo.edu",        "MCA", 3, 75, 78, 74, 79, 76, 39, 83.5, 4.5, 8,  0),
]


def seed_demo_data_if_empty(app) -> int:
    """Seed demo students, ML predictions, and Student Portal accounts if DB has 0 students."""
    if Student.query.count() > 0:
        return 0
    return _populate_demo_records(app)


def reset_demo_data(app) -> int:
    """Clear existing student/prediction/portal rows and re-seed fresh demo dataset."""
    StudentAuth.query.delete()
    PredictionLog.query.delete()
    Student.query.delete()
    db.session.commit()
    return _populate_demo_records(app)


def _populate_demo_records(app) -> int:
    now = datetime.utcnow()
    ready = ml_service.is_ready()
    inserted = 0

    for idx, row in enumerate(DEMO_STUDENTS):
        (
            sid, name, email, dept, sem,
            s1, s2, s3, s4, s5,
            internal, att, hrs, assign, backlogs,
        ) = row

        created_ts = now - timedelta(days=30 - idx, hours=(idx * 3) % 24)
        student = Student(
            student_id=sid,
            name=name,
            email=email,
            department=dept,
            semester=sem,
            subject1_marks=float(s1),
            subject2_marks=float(s2),
            subject3_marks=float(s3),
            subject4_marks=float(s4),
            subject5_marks=float(s5),
            internal_marks=float(internal),
            attendance_pct=float(att),
            study_hours_per_day=float(hrs),
            assignments_submitted=int(assign),
            previous_backlogs=int(backlogs),
            created_at=created_ts,
            updated_at=created_ts,
        )
        db.session.add(student)
        db.session.flush()

        if ready:
            feat_vec = student.feature_vector()
            pred = ml_service.predict(feat_vec)
            log = PredictionLog(
                student_id=student.id,
                result=pred["result"],
                pass_probability=pred["pass_probability"],
                fail_probability=pred["fail_probability"],
                model_name=pred["model_name"],
                model_version=pred["model_version"],
                feature_snapshot=dict(zip(
                    ["s1", "s2", "s3", "s4", "s5", "internal", "attendance",
                     "study_hrs", "assignments", "backlogs", "avg"],
                    feat_vec,
                )),
                predicted_at=now - timedelta(hours=(len(DEMO_STUDENTS) - idx) * 4),
            )
            db.session.add(log)

        # Provision self-service portal accounts for the first 12 students
        if idx < 12:
            auth = StudentAuth(
                student_id=student.id,
                username=sid,
                is_active=True,
                created_at=created_ts,
            )
            auth.set_password(sid)
            db.session.add(auth)

        inserted += 1

    db.session.commit()
    app.logger.info(f"✅  Seeded {inserted} demo student records with ML predictions & portal accounts.")
    return inserted
