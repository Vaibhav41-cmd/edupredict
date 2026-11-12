"""
app/services/ml_service.py — Machine Learning Service Layer

Responsibilities:
  - Load trained models from disk (lazy, cached)
  - Run predictions with probability scores
  - Expose model metadata and evaluation metrics
  - Retrain models on demand

All ML logic is isolated here; routes never touch sklearn directly.
"""

import os
import logging
import numpy as np
import joblib
from typing import Optional
from flask import current_app

logger = logging.getLogger(__name__)

# ── Feature order MUST match training order in ml/train.py ──────────────────
FEATURE_NAMES = [
    "subject1_marks",
    "subject2_marks",
    "subject3_marks",
    "subject4_marks",
    "subject5_marks",
    "internal_marks",
    "attendance_pct",
    "study_hours_per_day",
    "assignments_submitted",
    "previous_backlogs",
    "average_marks",
]


class MLService:
    """
    Singleton-style service that wraps all ML operations.
    Implements lazy loading — models are loaded once and cached.
    """

    _instance: Optional["MLService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._model = None
        self._scaler = None
        self._metadata = None
        self._initialized = True

    # ── Model Directory ────────────────────────────────────────────────────────

    def _model_dir(self) -> str:
        try:
            return current_app.config["MODEL_DIR"]
        except RuntimeError:
            return os.path.join(os.path.dirname(__file__), "..", "..", "ml", "saved_models")

    def _path(self, filename: str) -> str:
        return os.path.join(self._model_dir(), filename)

    # ── Lazy Loading ───────────────────────────────────────────────────────────

    def _load_artifacts(self) -> bool:
        """Load model, scaler, and metadata from disk. Returns True on success."""
        try:
            model_path = self._path("best_model.joblib")
            scaler_path = self._path("scaler.joblib")
            meta_path = self._path("model_metadata.joblib")

            if not all(os.path.exists(p) for p in [model_path, scaler_path, meta_path]):
                logger.warning("Model artifacts not found. Run ml/train.py first.")
                return False

            self._model = joblib.load(model_path)
            self._scaler = joblib.load(scaler_path)
            self._metadata = joblib.load(meta_path)
            logger.info(f"Loaded model: {self._metadata.get('best_model_name')}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model artifacts: {e}")
            self._model = None
            self._scaler = None
            self._metadata = None
            return False

    def is_ready(self) -> bool:
        """Check if the ML model is loaded and ready."""
        if self._model is None:
            return self._load_artifacts()
        return True

    def reset(self) -> None:
        """Force reload of model on next call (use after retraining)."""
        self._model = None
        self._scaler = None
        self._metadata = None
        logger.info("MLService cache cleared. Model will reload on next request.")

    # ── Core Prediction ────────────────────────────────────────────────────────

    def predict(self, feature_vector: list) -> dict:
        """
        Run prediction on a single student's feature vector.

        Args:
            feature_vector: Ordered list of 11 numeric features.

        Returns:
            dict with keys: result, pass_probability, fail_probability,
                            model_name, model_version, confidence_level
        """
        if not self.is_ready():
            raise RuntimeError(
                "ML model is not available. Please train the model first by running ml/train.py"
            )

        try:
            X = np.array(feature_vector).reshape(1, -1)
            X_scaled = self._scaler.transform(X)

            prediction = self._model.predict(X_scaled)[0]
            probabilities = self._model.predict_proba(X_scaled)[0]

            # Assumes class order: [0=FAIL, 1=PASS]
            fail_prob = float(probabilities[0])
            pass_prob = float(probabilities[1])

            result = "PASS" if int(prediction) == 1 else "FAIL"
            confidence = self._get_confidence_label(max(pass_prob, fail_prob))

            return {
                "result": result,
                "pass_probability": pass_prob,
                "fail_probability": fail_prob,
                "model_name": self._metadata.get("best_model_name", "Unknown"),
                "model_version": self._metadata.get("version", "1.0"),
                "confidence_level": confidence,
                "feature_importance": self._get_top_features(),
            }

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise RuntimeError(f"Prediction failed: {str(e)}")

    @staticmethod
    def _get_confidence_label(probability: float) -> str:
        if probability >= 0.90:
            return "Very High"
        elif probability >= 0.75:
            return "High"
        elif probability >= 0.60:
            return "Moderate"
        else:
            return "Low"

    def _get_top_features(self) -> list:
        """Return top 5 normalized feature importances (supports tree & linear models)."""
        try:
            model = self._model
            if hasattr(model, "named_steps"):
                clf = model.named_steps.get("clf", model)
            else:
                clf = model

            importances = None
            if hasattr(clf, "feature_importances_"):
                importances = np.asarray(clf.feature_importances_, dtype=float)
            elif hasattr(clf, "coef_"):
                weights = np.abs(np.asarray(clf.coef_[0], dtype=float))
                total = weights.sum()
                importances = (weights / total) if total > 0 else weights

            if importances is not None:
                indices = np.argsort(importances)[::-1][:5]
                return [
                    {"feature": FEATURE_NAMES[i], "importance": round(float(importances[i]), 4)}
                    for i in indices
                ]
        except Exception:
            pass
        return []

    # ── Model Metadata & Metrics ───────────────────────────────────────────────

    def get_metrics(self) -> dict:
        """Return all stored evaluation metrics for the dashboard."""
        if not self.is_ready():
            return {"error": "Model not loaded"}
        return self._metadata.copy()

    def get_model_comparison(self) -> list:
        """Return per-model comparison table."""
        if not self.is_ready():
            return []
        return self._metadata.get("model_comparison", [])

    def get_confusion_matrix(self) -> dict:
        """Return confusion matrix data."""
        if not self.is_ready():
            return {}
        return self._metadata.get("confusion_matrix", {})


# ── Module-level singleton ─────────────────────────────────────────────────────
ml_service = MLService()
