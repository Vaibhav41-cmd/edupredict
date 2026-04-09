"""
run.py — Application Entry Point

Usage:
  python run.py              # development server
  gunicorn run:app           # production (gunicorn)
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    print(f"""
╔══════════════════════════════════════════════════════╗
║   Student Pass/Fail Prediction System                ║
║   ML-powered Academic Analytics Dashboard            ║
╠══════════════════════════════════════════════════════╣
║  → http://localhost:{port}                              ║
║  → Default login: admin / Admin@1234                 ║
║                                                      ║
║  FIRST TIME SETUP:                                   ║
║  1. python ml/train.py    (train the ML model)       ║
║  2. python run.py         (start the server)         ║
╚══════════════════════════════════════════════════════╝
    """)

    app.run(host="0.0.0.0", port=port, debug=debug)
