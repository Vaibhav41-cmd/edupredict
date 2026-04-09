# Student Pass/Fail Prediction System
## MCA Final Year Project | Machine Learning + Flask + MySQL

---

## 📁 Project Structure

```
student_prediction_system/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models/
│   │   ├── user.py              # Admin user model (Flask-Login)
│   │   └── student.py          # Student + PredictionLog models
│   ├── routes/
│   │   ├── auth.py              # Login / Logout
│   │   ├── dashboard.py         # Admin dashboard
│   │   ├── students.py          # Student CRUD
│   │   ├── predictions.py       # Prediction history
│   │   └── api.py               # REST API (v1)
│   ├── services/
│   │   └── ml_service.py        # ML prediction service (singleton)
│   └── utils/
│       ├── logger.py            # Rotating file logger
│       └── validators.py        # Input validation
├── ml/
│   ├── train.py                 # Model training pipeline
│   ├── student_data.csv         # Training data (auto-generated)
│   └── saved_models/
│       ├── best_model.joblib    # Best ML model
│       ├── scaler.joblib        # Feature scaler
│       └── model_metadata.joblib
├── frontend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── students/
│   │   │   ├── list.html, add.html, view.html, edit.html
│   │   └── predictions/
│   │       └── list.html
│   └── static/css/, js/
├── database/
│   └── schema.sql               # MySQL DDL + sample data
├── logs/
│   └── app.log                  # Rotating application log
├── config.py                    # Multi-environment config
├── run.py                       # Entry point
├── requirements.txt
└── .env.example                 # Environment variable template
```

---

## ⚙️ Setup Guide (Step by Step)

### Prerequisites
- Python 3.10+
- XAMPP (MySQL + Apache)
- Git

---

### Step 1 — Clone & Create Virtual Environment

```bash
cd C:/xampp/htdocs   # or any directory
git clone <repo-url> student_prediction_system
cd student_prediction_system

python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings:
#   DB_PASSWORD=  (leave blank for XAMPP default)
#   SECRET_KEY=   (set a random 32+ char string)
```

### Step 4 — Setup MySQL Database

1. Start XAMPP → Start MySQL + Apache
2. Open **phpMyAdmin** → http://localhost/phpmyadmin
3. Click **Import** → select `database/schema.sql` → Go

OR via command line:
```bash
mysql -u root -p < database/schema.sql
```

### Step 5 — Train the ML Model

```bash
python ml/train.py
```

Expected output:
```
MODEL TRAINING & EVALUATION
════════════════════════════
▶  Training: Logistic Regression   Accuracy=0.8800 ...
▶  Training: Random Forest         Accuracy=0.9250 ...
▶  Training: Gradient Boosting     Accuracy=0.9100 ...
▶  Training: SVM                   Accuracy=0.8950 ...

🏆  Best model: Random Forest (ROC-AUC=0.9712)
✅  All artifacts saved to: ml/saved_models
```

### Step 6 — Run the Application

```bash
python run.py
```

Open **http://localhost:5000** in your browser.

**Default Login:**
- Username: `admin`
- Password: `Admin@1234`

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | System health check |
| GET | `/api/v1/students` | List all students (paginated) |
| GET | `/api/v1/students/<id>` | Get single student |
| POST | `/api/v1/students/<id>/predict` | Re-run prediction |
| POST | `/api/v1/predict/quick` | Quick prediction (no DB storage) |
| GET | `/api/v1/model/metrics` | ML model metrics & comparison |
| GET | `/api/v1/stats/summary` | Dashboard summary stats |

---

## 🤖 ML Features (Input Variables)

| Feature | Range | Weight |
|---------|-------|--------|
| Subject 1–5 Marks | 0–100 | 35% |
| Internal Marks | 0–50 | 20% |
| Attendance % | 0–100 | 25% |
| Study Hours/Day | 0–18 | 10% |
| Assignments Submitted | 0–10 | 5% |
| Previous Backlogs | 0–20 | -5% |
| Average Marks | derived | used |

## 🔬 Models Compared

| Model | Type | Key Strength |
|-------|------|-------------|
| Logistic Regression | Linear | Fast, interpretable |
| Random Forest | Ensemble | High accuracy, robust |
| Gradient Boosting | Boosting | Best for imbalanced data |
| SVM (RBF) | Kernel | Good with small datasets |

**Selection Criterion:** Best ROC-AUC score on 20% holdout test set + 5-fold cross-validation.

---

## ❓ Viva Questions & Answers

**Q1. What ML algorithm did you choose and why?**
A: We trained Logistic Regression, Random Forest, Gradient Boosting, and SVM, then selected the best via ROC-AUC. Random Forest typically wins because it handles non-linear feature interactions and is robust to outliers. We use 5-fold stratified cross-validation to ensure the selection isn't biased by one random split.

**Q2. What is cross-validation and why do you use it?**
A: Cross-validation (k-fold) splits the training data into k subsets, trains on k-1 and validates on 1, rotating until every subset is used. This gives a more reliable estimate of generalization performance than a single train/test split.

**Q3. Explain the confusion matrix.**
A: A 2×2 matrix showing TP (correctly predicted PASS), TN (correctly predicted FAIL), FP (predicted PASS but actually FAIL), FN (predicted FAIL but actually PASS). From it we derive Precision = TP/(TP+FP) and Recall = TP/(TP+FN).

**Q4. What is ROC-AUC?**
A: The ROC curve plots True Positive Rate vs False Positive Rate at all classification thresholds. AUC (Area Under Curve) = 1.0 is a perfect classifier; 0.5 is random. We use it as our primary model-selection metric because it's threshold-independent.

**Q5. What is feature scaling and why is it needed?**
A: Feature scaling (StandardScaler: z = (x-μ)/σ) ensures all features contribute equally to distance-based or gradient-based models. Without it, attendance (0–100) would dominate over backlogs (0–10) even if backlogs is more predictive.

**Q6. How does Flask-Login work?**
A: Flask-Login stores the user's ID in a secure, signed session cookie. The `@login_required` decorator on routes checks if a valid session exists; if not, it redirects to the login page. Passwords are hashed with PBKDF2-SHA256 via Werkzeug.

**Q7. What is the MVC pattern in this project?**
A: Models = SQLAlchemy ORM classes (app/models/). Views = Jinja2 HTML templates (frontend/templates/). Controllers = Flask Blueprint route functions (app/routes/). The ML service layer (app/services/) handles business logic, keeping routes thin.

**Q8. How do you prevent SQL injection?**
A: SQLAlchemy's ORM uses parameterized queries internally — never string-concatenated SQL. All user input goes through validator functions before being passed to the ORM.

**Q9. What is joblib used for?**
A: joblib is scikit-learn's recommended serialization library for saving ML models. It's more efficient than pickle for large NumPy arrays because it uses memory-mapped files.

**Q10. What is the difference between precision and recall?**
A: Precision = of all predicted PASS, how many actually passed (avoids false alarms). Recall = of all actual PASS, how many did we catch (avoids missing at-risk students). In education, recall is more critical — missing a student who will fail is worse than a false alarm.

---

## 🚀 Future Scope

1. **Deep Learning** — LSTM for time-series performance tracking across semesters
2. **Explainable AI (XAI)** — SHAP values to show which feature influenced each student's prediction
3. **Email Alerts** — Auto-notify at-risk students (attendance < 75%, avg marks < 40)
4. **Data Import** — Bulk CSV/Excel upload for registrar office integration
5. **Student Portal** — Separate read-only login for students to view their own prediction
6. **Mobile App** — React Native / Flutter frontend consuming the existing REST API
7. **Federated Learning** — Train across multiple college branches without sharing raw data
8. **A/B Testing** — Compare model versions in production with gradual rollout
9. **Power BI / Tableau Integration** — Connect to the MySQL DB for institutional dashboards
10. **Docker Deployment** — Containerize with docker-compose (Flask + MySQL + Nginx)
