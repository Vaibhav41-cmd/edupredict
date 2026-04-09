# app/models/__init__.py
from app.models.user import Admin
from app.models.student import Student, PredictionLog

__all__ = ["Admin", "Student", "PredictionLog"]
