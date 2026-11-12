"""
tests/test_demo_app.py — End-to-End Integration Tests for EduPredict Demo Version
"""

import os
import pytest
from app import create_app, db
from config import DemoConfig


@pytest.fixture
def demo_client(tmp_path):
    class TestDemoConfig(DemoConfig):
        TESTING = True
        WTF_CSRF_ENABLED = False
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test_demo.db'}"

    app = create_app(TestDemoConfig)
    with app.test_client() as client:
        yield client


def test_demo_seeding_and_public_page(demo_client):
    root = demo_client.get("/", follow_redirects=False)
    assert root.status_code == 302 and root.headers["Location"].endswith("/demo/")
    res = demo_client.get("/demo/")
    assert res.status_code == 200
    assert b"EduPredict" in res.data
    assert b"30" in res.data


def test_demo_live_predict_api(demo_client):
    payload = {
        "subject1_marks": 85,
        "subject2_marks": 88,
        "subject3_marks": 82,
        "subject4_marks": 90,
        "subject5_marks": 84,
        "internal_marks": 44,
        "attendance_pct": 92.0,
        "study_hours_per_day": 6.0,
        "assignments_submitted": 9,
        "previous_backlogs": 0,
    }
    res = demo_client.post("/demo/api/predict", json=payload)
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert body["data"]["result"] == "PASS"
    assert len(body["data"]["feature_importance"]) > 0


def test_one_click_admin_demo_and_all_views(demo_client):
    res = demo_client.post("/demo/login/admin", follow_redirects=True)
    assert res.status_code == 200
    assert b"Total Students" in res.data

    for path in ["/students/", "/students/1", "/predictions/", "/alerts/", "/bulk/upload", "/chatbot/", "/api/v1/health", "/api/v1/stats/summary"]:
        r = demo_client.get(path)
        assert r.status_code == 200, f"Failed on {path}"

    chat_res = demo_client.post("/chatbot/api/message", json={"message": "9"})
    assert chat_res.status_code == 200
    assert chat_res.get_json()["success"] is True


def test_report_and_presentation_download_routes(demo_client):
    from pathlib import Path
    report_dir = Path(__file__).resolve().parents[1] / "report"
    assert (report_dir / "EduPredict_MCA521_Project_Report.pdf").exists()
    assert (report_dir / "EduPredict_MCA521_Project_Report.docx").exists()
    assert (report_dir / "EduPredict_MCA521_Presentation.pptx").exists()
    assert demo_client.get("/demo/report/pdf").status_code == 200
    assert demo_client.get("/demo/report/docx").status_code == 200
    ppt = demo_client.get("/demo/report/pptx")
    assert ppt.status_code == 200
    assert "presentationml.presentation" in ppt.content_type


def test_one_click_student_portal_demo(demo_client):
    res = demo_client.post("/demo/login/student/MCA2024001", follow_redirects=True)
    assert res.status_code == 200
    assert b"Rahul Sharma" in res.data
    assert b"PASS" in res.data
