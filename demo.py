"""
demo.py — Zero-Setup Interactive Demo Launcher for EduPredict (MCA-521)

Starts EduPredict in SQLite Demo Mode (no XAMPP/MySQL required),
automatically trains ML models if missing, seeds 30 realistic student
profiles + predictions + Student Portal accounts, and binds to 0.0.0.0.

Usage:
  python demo.py
"""

import os
import subprocess
import sys

os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("FLASK_ENV", "demo")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "ml", "saved_models", "best_model.joblib")

if not os.path.exists(MODEL_FILE):
    print("⚙️  ML artifacts not found — training models now...")
    subprocess.check_call([sys.executable, os.path.join(BASE_DIR, "ml", "train.py")])

from app import create_app
from config import DemoConfig

app = create_app(DemoConfig)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║   EduPredict — Interactive Demo Version (MCA-521 Project)        ║
║   Zero-Setup SQLite Mode · 30 Seeded Students · 4 ML Classifiers ║
╠══════════════════════════════════════════════════════════════════╣
║  → Live App URL     : http://0.0.0.0:{port}                         ║
║  → Interactive Demo : /demo                                      ║
║  → Admin Login      : admin / Admin@1234                         ║
║  → Student (PASS)   : MCA2024001 / MCA2024001                    ║
║  → Student (FAIL)   : MCA2024004 / MCA2024004                    ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    app.run(host="0.0.0.0", port=port, debug=debug)
