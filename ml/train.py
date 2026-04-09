"""
ml/train.py — Model Training Pipeline

This script:
  1. Generates (or loads) training data
  2. Preprocesses and engineers features
  3. Trains multiple classifiers (LR, RF, SVM, GB)
  4. Evaluates and compares models
  5. Saves the best model, scaler, and metadata to disk

Run: python ml/train.py
"""

import os
import sys
import logging
import warnings
import numpy as np
import pandas as pd
import joblib
from datetime import datetime

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "saved_models")
DATA_PATH = os.path.join(SCRIPT_DIR, "student_data.csv")
os.makedirs(MODEL_DIR, exist_ok=True)

# ── Feature columns (MUST match app/services/ml_service.py FEATURE_NAMES) ─────
FEATURE_COLS = [
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
TARGET_COL = "result"  # 1 = PASS, 0 = FAIL


# ══════════════════════════════════════════════════════════════════════════════
# 1. DATA GENERATION / LOADING
# ══════════════════════════════════════════════════════════════════════════════

def generate_synthetic_data(n_samples: int = 2000, seed: int = 42) -> pd.DataFrame:
    """
    Generate realistic synthetic student data.
    The pass/fail label is computed from a weighted rule, then slightly
    noisified to simulate real-world messiness.
    """
    rng = np.random.default_rng(seed)
    logger.info(f"Generating {n_samples} synthetic student records…")

    s1 = rng.uniform(20, 100, n_samples)
    s2 = rng.uniform(20, 100, n_samples)
    s3 = rng.uniform(20, 100, n_samples)
    s4 = rng.uniform(20, 100, n_samples)
    s5 = rng.uniform(20, 100, n_samples)
    avg = (s1 + s2 + s3 + s4 + s5) / 5

    internal = rng.uniform(10, 50, n_samples)
    attendance = rng.uniform(30, 100, n_samples)
    study_hrs = rng.uniform(0, 10, n_samples)
    assignments = rng.integers(0, 11, n_samples)
    backlogs = rng.integers(0, 8, n_samples)

    # Deterministic pass rule (weighted scoring)
    score = (
        0.35 * (avg / 100)
        + 0.20 * (internal / 50)
        + 0.25 * (attendance / 100)
        + 0.10 * (study_hrs / 10)
        + 0.05 * (assignments / 10)
        - 0.05 * (backlogs / 7)
    )

    # Add realistic noise
    score += rng.normal(0, 0.05, n_samples)

    # Threshold: score > 0.50 → PASS
    result = (score > 0.50).astype(int)

    df = pd.DataFrame({
        "subject1_marks": s1,
        "subject2_marks": s2,
        "subject3_marks": s3,
        "subject4_marks": s4,
        "subject5_marks": s5,
        "internal_marks": internal,
        "attendance_pct": attendance,
        "study_hours_per_day": study_hrs,
        "assignments_submitted": assignments,
        "previous_backlogs": backlogs,
        "average_marks": avg,
        TARGET_COL: result,
    })

    logger.info(f"Class distribution — PASS: {result.sum()}, FAIL: {(result == 0).sum()}")
    return df


def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_PATH):
        logger.info(f"Loading existing data from {DATA_PATH}")
        return pd.read_csv(DATA_PATH)
    df = generate_synthetic_data()
    df.to_csv(DATA_PATH, index=False)
    logger.info(f"Saved synthetic data to {DATA_PATH}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# 2. PREPROCESSING & FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════════════

def preprocess(df: pd.DataFrame):
    """
    - Clip values to valid ranges
    - Drop rows with nulls
    - Compute/verify derived features
    - Split into X, y
    """
    df = df.copy()
    df.dropna(inplace=True)

    # Clip to valid ranges
    for col in ["subject1_marks", "subject2_marks", "subject3_marks",
                "subject4_marks", "subject5_marks"]:
        df[col] = df[col].clip(0, 100)
    df["internal_marks"] = df["internal_marks"].clip(0, 50)
    df["attendance_pct"] = df["attendance_pct"].clip(0, 100)
    df["study_hours_per_day"] = df["study_hours_per_day"].clip(0, 18)
    df["assignments_submitted"] = df["assignments_submitted"].clip(0, 10)
    df["previous_backlogs"] = df["previous_backlogs"].clip(0, 20)

    # Ensure average_marks exists
    if "average_marks" not in df.columns:
        mark_cols = ["subject1_marks", "subject2_marks", "subject3_marks",
                     "subject4_marks", "subject5_marks"]
        df["average_marks"] = df[mark_cols].mean(axis=1)

    X = df[FEATURE_COLS].values.astype(float)
    y = df[TARGET_COL].values.astype(int)
    return X, y


# ══════════════════════════════════════════════════════════════════════════════
# 3. MODEL DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_models() -> dict:
    """Return dict of model_name → sklearn estimator."""
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=1000, C=1.0, solver="lbfgs", random_state=42
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=4,
            random_state=42,
        ),
        "SVM": SVC(
            kernel="rbf",
            C=1.0,
            probability=True,
            random_state=42,
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. TRAINING & EVALUATION
# ══════════════════════════════════════════════════════════════════════════════

def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray, name: str) -> dict:
    """Compute full evaluation metrics for one model."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    metrics = {
        "model_name": name,
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        "confusion_matrix": {
            "tn": int(tn), "fp": int(fp),
            "fn": int(fn), "tp": int(tp),
        },
        "classification_report": classification_report(
            y_test, y_pred, target_names=["FAIL", "PASS"], output_dict=True
        ),
    }
    return metrics


def train_and_compare(X_train, X_test, y_train, y_test, scaler) -> tuple:
    """
    Train all models, evaluate, and return:
      (best_model, all_metrics_list, best_model_name)
    """
    models = get_models()
    results = []
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    X_train_sc = scaler.transform(X_train)
    X_test_sc = scaler.transform(X_test)

    best_model = None
    best_name = None
    best_roc = -1

    logger.info("\n" + "═" * 60)
    logger.info("  MODEL TRAINING & EVALUATION")
    logger.info("═" * 60)

    for name, model in models.items():
        logger.info(f"\n▶  Training: {name}")
        model.fit(X_train_sc, y_train)

        # 5-fold cross-validation accuracy
        cv_scores = cross_val_score(model, X_train_sc, y_train, cv=cv, scoring="accuracy")

        metrics = evaluate_model(model, X_test_sc, y_test, name)
        metrics["cv_mean"] = round(cv_scores.mean(), 4)
        metrics["cv_std"] = round(cv_scores.std(), 4)

        logger.info(
            f"   Accuracy={metrics['accuracy']:.4f} | "
            f"Precision={metrics['precision']:.4f} | "
            f"Recall={metrics['recall']:.4f} | "
            f"F1={metrics['f1_score']:.4f} | "
            f"ROC-AUC={metrics['roc_auc']:.4f} | "
            f"CV={metrics['cv_mean']:.4f} ±{metrics['cv_std']:.4f}"
        )

        results.append(metrics)

        if metrics["roc_auc"] > best_roc:
            best_roc = metrics["roc_auc"]
            best_model = model
            best_name = name

    logger.info(f"\n🏆  Best model: {best_name} (ROC-AUC={best_roc:.4f})")
    return best_model, results, best_name


# ══════════════════════════════════════════════════════════════════════════════
# 5. SAVE ARTIFACTS
# ══════════════════════════════════════════════════════════════════════════════

def save_artifacts(best_model, scaler, results, best_name, X_test, y_test):
    """Persist model, scaler, and all metadata to disk."""

    # Save model
    joblib.dump(best_model, os.path.join(MODEL_DIR, "best_model.joblib"))
    # Save scaler
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.joblib"))

    # Identify best model's full metrics
    best_metrics = next((r for r in results if r["model_name"] == best_name), {})

    # Build serializable comparison table
    comparison = [
        {
            "model_name": r["model_name"],
            "accuracy": r["accuracy"],
            "precision": r["precision"],
            "recall": r["recall"],
            "f1_score": r["f1_score"],
            "roc_auc": r["roc_auc"],
            "cv_mean": r.get("cv_mean", 0),
            "cv_std": r.get("cv_std", 0),
        }
        for r in results
    ]

    metadata = {
        "best_model_name": best_name,
        "version": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "trained_at": datetime.now().isoformat(),
        "feature_names": FEATURE_COLS,
        "n_features": len(FEATURE_COLS),
        "accuracy": best_metrics.get("accuracy"),
        "precision": best_metrics.get("precision"),
        "recall": best_metrics.get("recall"),
        "f1_score": best_metrics.get("f1_score"),
        "roc_auc": best_metrics.get("roc_auc"),
        "cv_mean": best_metrics.get("cv_mean"),
        "cv_std": best_metrics.get("cv_std"),
        "confusion_matrix": best_metrics.get("confusion_matrix"),
        "classification_report": best_metrics.get("classification_report"),
        "model_comparison": comparison,
    }

    joblib.dump(metadata, os.path.join(MODEL_DIR, "model_metadata.joblib"))
    logger.info(f"\n✅  All artifacts saved to: {MODEL_DIR}")
    return metadata


# ══════════════════════════════════════════════════════════════════════════════
# 6. MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    logger.info("=" * 60)
    logger.info("  STUDENT PASS/FAIL PREDICTION — TRAINING PIPELINE")
    logger.info("=" * 60)

    # Load data
    df = load_data()
    X, y = preprocess(df)
    logger.info(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )
    logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # Scale
    scaler = StandardScaler()
    scaler.fit(X_train)

    # Train & compare
    best_model, results, best_name = train_and_compare(
        X_train, X_test, y_train, y_test, scaler
    )

    # Save
    metadata = save_artifacts(best_model, scaler, results, best_name, X_test, y_test)

    logger.info("\n" + "═" * 60)
    logger.info(f"  FINAL RESULTS — {best_name}")
    logger.info("═" * 60)
    logger.info(f"  Accuracy  : {metadata['accuracy']:.4f}")
    logger.info(f"  Precision : {metadata['precision']:.4f}")
    logger.info(f"  Recall    : {metadata['recall']:.4f}")
    logger.info(f"  F1 Score  : {metadata['f1_score']:.4f}")
    logger.info(f"  ROC-AUC   : {metadata['roc_auc']:.4f}")
    logger.info("=" * 60)
    logger.info("\n  Run: python run.py   to start the web server.\n")


if __name__ == "__main__":
    main()
