"""
tests/test_ml_pipeline.py — ML Pipeline Unit Tests

Tests the training, prediction, and validation layers independently
(no DB required — uses SQLite in-memory for model tests).

Run:
  python -m pytest tests/ -v
"""

import os
import sys
import pytest
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ════════════════════════════════════════════════════════════════════════
# 1. VALIDATOR TESTS
# ════════════════════════════════════════════════════════════════════════

class TestValidators:

    def test_valid_marks_pass(self):
        from app.utils.validators import validate_marks
        ok, msg = validate_marks(75.5, "Subject 1")
        assert ok is True
        assert msg is None

    def test_marks_below_zero_fail(self):
        from app.utils.validators import validate_marks
        ok, msg = validate_marks(-5, "Subject 1")
        assert ok is False
        assert "0" in msg

    def test_marks_above_100_fail(self):
        from app.utils.validators import validate_marks
        ok, msg = validate_marks(101, "Subject 1")
        assert ok is False

    def test_valid_attendance_pass(self):
        from app.utils.validators import validate_attendance
        ok, msg = validate_attendance(85.0)
        assert ok is True

    def test_attendance_over_100_fail(self):
        from app.utils.validators import validate_attendance
        ok, msg = validate_attendance(105.0)
        assert ok is False

    def test_valid_email(self):
        from app.utils.validators import validate_email
        ok, _ = validate_email("student@college.edu")
        assert ok is True

    def test_invalid_email(self):
        from app.utils.validators import validate_email
        ok, _ = validate_email("not-an-email")
        assert ok is False

    def test_student_id_uppercase_valid(self):
        from app.utils.validators import validate_student_id
        ok, _ = validate_student_id("MCA2024001")
        assert ok is True

    def test_student_id_spaces_invalid(self):
        from app.utils.validators import validate_student_id
        ok, _ = validate_student_id("MCA 2024")
        assert ok is False

    def test_full_form_valid(self):
        from app.utils.validators import validate_student_form
        data = {
            "student_id": "MCA2024001",
            "name": "Test Student",
            "email": "test@demo.com",
            "department": "MCA",
            "semester": 2,
            "subject1_marks": 75, "subject2_marks": 80,
            "subject3_marks": 70, "subject4_marks": 68,
            "subject5_marks": 77,
            "internal_marks": 38,
            "attendance_pct": 82,
            "study_hours_per_day": 4.5,
            "assignments_submitted": 8,
            "previous_backlogs": 1,
        }
        ok, errors = validate_student_form(data)
        assert ok is True, f"Unexpected errors: {errors}"

    def test_full_form_missing_name(self):
        from app.utils.validators import validate_student_form
        data = {
            "student_id": "MCA001", "name": "",
            "email": "test@demo.com", "department": "MCA", "semester": 2,
            "subject1_marks": 75, "subject2_marks": 80, "subject3_marks": 70,
            "subject4_marks": 68, "subject5_marks": 77,
            "internal_marks": 38, "attendance_pct": 82,
            "study_hours_per_day": 4.5, "assignments_submitted": 8, "previous_backlogs": 1,
        }
        ok, errors = validate_student_form(data)
        assert ok is False
        assert any("name" in e.lower() for e in errors)


# ════════════════════════════════════════════════════════════════════════
# 2. ML DATA GENERATION TESTS
# ════════════════════════════════════════════════════════════════════════

class TestDataGeneration:

    def test_generate_correct_shape(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml"))
        from ml.train import generate_synthetic_data
        df = generate_synthetic_data(n_samples=100, seed=1)
        assert df.shape[0] == 100
        assert "result" in df.columns

    def test_marks_within_range(self):
        from ml.train import generate_synthetic_data
        df = generate_synthetic_data(n_samples=200, seed=2)
        for col in ["subject1_marks", "subject2_marks", "subject3_marks",
                    "subject4_marks", "subject5_marks"]:
            assert df[col].between(0, 100).all(), f"{col} out of range"

    def test_attendance_within_range(self):
        from ml.train import generate_synthetic_data
        df = generate_synthetic_data(n_samples=200, seed=3)
        assert df["attendance_pct"].between(0, 100).all()

    def test_class_balance_reasonable(self):
        from ml.train import generate_synthetic_data
        df = generate_synthetic_data(n_samples=1000, seed=42)
        pass_rate = df["result"].mean()
        # Should be between 40% and 80% (not degenerate)
        assert 0.40 <= pass_rate <= 0.80, f"Pass rate {pass_rate:.2f} seems off"

    def test_preprocess_removes_nulls(self):
        from ml.train import generate_synthetic_data, preprocess
        import pandas as pd
        df = generate_synthetic_data(n_samples=100)
        # Inject nulls
        df.loc[0, "subject1_marks"] = float("nan")
        X, y = preprocess(df)
        assert X.shape[0] == 99  # one row dropped

    def test_preprocess_clips_values(self):
        from ml.train import generate_synthetic_data, preprocess
        df = generate_synthetic_data(n_samples=50)
        df.loc[0, "subject1_marks"] = 120  # out of range
        df.loc[1, "attendance_pct"] = -5
        X, y = preprocess(df)
        # After clipping, values should be within range
        assert X[:, 0].max() <= 100
        assert X[:, 6].min() >= 0  # attendance column


# ════════════════════════════════════════════════════════════════════════
# 3. MODEL TRAINING TESTS
# ════════════════════════════════════════════════════════════════════════

class TestModelTraining:

    @pytest.fixture(scope="class")
    def trained_artifacts(self, tmp_path_factory):
        """Train models once and share across tests in this class."""
        from ml.train import generate_synthetic_data, preprocess, get_models, train_and_compare
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler

        tmp = tmp_path_factory.mktemp("models")
        df = generate_synthetic_data(n_samples=500, seed=99)
        X, y = preprocess(df)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
        scaler = StandardScaler()
        scaler.fit(X_train)
        best_model, results, best_name = train_and_compare(X_train, X_test, y_train, y_test, scaler)
        return {"model": best_model, "scaler": scaler, "results": results, "best_name": best_name,
                "X_test": X_test, "y_test": y_test}

    def test_all_models_trained(self, trained_artifacts):
        results = trained_artifacts["results"]
        assert len(results) == 4  # LR, RF, GB, SVM

    def test_best_model_accuracy_above_threshold(self, trained_artifacts):
        results = trained_artifacts["results"]
        best = max(results, key=lambda r: r["roc_auc"])
        assert best["accuracy"] >= 0.70, f"Accuracy too low: {best['accuracy']}"

    def test_metrics_keys_present(self, trained_artifacts):
        for result in trained_artifacts["results"]:
            for key in ["accuracy", "precision", "recall", "f1_score", "roc_auc"]:
                assert key in result, f"Missing metric '{key}' in {result['model_name']}"

    def test_confusion_matrix_present(self, trained_artifacts):
        for result in trained_artifacts["results"]:
            cm = result.get("confusion_matrix", {})
            assert all(k in cm for k in ["tp", "tn", "fp", "fn"])

    def test_prediction_is_binary(self, trained_artifacts):
        model = trained_artifacts["model"]
        scaler = trained_artifacts["scaler"]
        X_test = trained_artifacts["X_test"]
        X_scaled = scaler.transform(X_test)
        preds = model.predict(X_scaled)
        assert set(preds).issubset({0, 1})

    def test_predict_proba_sums_to_one(self, trained_artifacts):
        model = trained_artifacts["model"]
        scaler = trained_artifacts["scaler"]
        X_test = trained_artifacts["X_test"][:10]
        X_scaled = scaler.transform(X_test)
        probas = model.predict_proba(X_scaled)
        sums = probas.sum(axis=1)
        np.testing.assert_allclose(sums, np.ones(10), atol=1e-6)


# ════════════════════════════════════════════════════════════════════════
# 4. ML SERVICE TESTS (using saved models)
# ════════════════════════════════════════════════════════════════════════

class TestMLService:

    VALID_FEATURE_VECTOR = [75, 80, 72, 68, 77, 38, 82, 4.5, 8, 1, 74.4]

    def test_service_is_singleton(self):
        from app.services.ml_service import MLService
        s1 = MLService()
        s2 = MLService()
        assert s1 is s2

    def test_predict_returns_dict_with_required_keys(self):
        from app.services.ml_service import ml_service
        if not ml_service.is_ready():
            pytest.skip("Model not trained yet — run ml/train.py first")
        result = ml_service.predict(self.VALID_FEATURE_VECTOR)
        for key in ["result", "pass_probability", "fail_probability", "model_name"]:
            assert key in result, f"Missing key: {key}"

    def test_prediction_result_is_pass_or_fail(self):
        from app.services.ml_service import ml_service
        if not ml_service.is_ready():
            pytest.skip("Model not trained yet")
        result = ml_service.predict(self.VALID_FEATURE_VECTOR)
        assert result["result"] in ("PASS", "FAIL")

    def test_probabilities_sum_to_one(self):
        from app.services.ml_service import ml_service
        if not ml_service.is_ready():
            pytest.skip("Model not trained yet")
        result = ml_service.predict(self.VALID_FEATURE_VECTOR)
        total = result["pass_probability"] + result["fail_probability"]
        assert abs(total - 1.0) < 1e-4, f"Probabilities don't sum to 1: {total}"

    def test_high_performer_predicts_pass(self):
        from app.services.ml_service import ml_service
        if not ml_service.is_ready():
            pytest.skip("Model not trained yet")
        # s1-s5=95, internal=48, att=98, hrs=8, assign=10, backlogs=0, avg=95
        result = ml_service.predict([95, 95, 95, 95, 95, 48, 98, 8, 10, 0, 95])
        assert result["result"] == "PASS"

    def test_low_performer_predicts_fail(self):
        from app.services.ml_service import ml_service
        if not ml_service.is_ready():
            pytest.skip("Model not trained yet")
        # s1-s5=25, internal=10, att=35, hrs=0.5, assign=1, backlogs=6, avg=25
        result = ml_service.predict([25, 25, 25, 25, 25, 10, 35, 0.5, 1, 6, 25])
        assert result["result"] == "FAIL"

    def test_get_metrics_returns_dict(self):
        from app.services.ml_service import ml_service
        if not ml_service.is_ready():
            pytest.skip("Model not trained yet")
        metrics = ml_service.get_metrics()
        assert isinstance(metrics, dict)
        assert "accuracy" in metrics

    def test_model_comparison_returns_list(self):
        from app.services.ml_service import ml_service
        if not ml_service.is_ready():
            pytest.skip("Model not trained yet")
        comparison = ml_service.get_model_comparison()
        assert isinstance(comparison, list)
        assert len(comparison) >= 2


# ════════════════════════════════════════════════════════════════════════
# 5. CONFIDENCE LABEL TESTS
# ════════════════════════════════════════════════════════════════════════

class TestConfidenceLabel:

    def test_very_high_confidence(self):
        from app.services.ml_service import MLService
        label = MLService._get_confidence_label(0.95)
        assert label == "Very High"

    def test_high_confidence(self):
        from app.services.ml_service import MLService
        assert MLService._get_confidence_label(0.82) == "High"

    def test_moderate_confidence(self):
        from app.services.ml_service import MLService
        assert MLService._get_confidence_label(0.65) == "Moderate"

    def test_low_confidence(self):
        from app.services.ml_service import MLService
        assert MLService._get_confidence_label(0.55) == "Low"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
