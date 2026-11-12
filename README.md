# EduPredict — Student Pass/Fail Prediction System

A working MCA Semester III research-project prototype that uses machine learning to estimate student PASS/FAIL outcomes from academic and engagement indicators. The application combines model evaluation with a Flask web interface, student records, prediction history, dashboards, and an interactive demo.

> **Academic context:** Master of Computer Applications (MCA), Semester III · **MCA-521: Research Project** · Faculty of Science and Technology, Kavayitri Bahinabai Chaudhari North Maharashtra University, Jalgaon. The report cover follows the supplied college reference: S.S.V.P. Sanstha’s Late Karmaveer Dr. P. R. Ghogrey Science College, Dhule, Department of Computer Science.

**Important:** Predictions are estimates for early academic support. They are not official grades, guarantees, or substitutes for faculty judgment. The included profiles and login credentials are demonstration data only.

## Project features

- **Interactive live predictor** at `/demo/` with presets, sliders, prediction probabilities, feature-importance cues, and academic recommendations.
- **Four-model evaluation:** Logistic Regression, RBF SVM, Gradient Boosting, and Random Forest. The saved Logistic Regression model is selected by ROC-AUC.
- **Student record management:** add, view, edit, and search student profiles.
- **Prediction history:** timestamped PASS/FAIL prediction logs, probabilities, model version, and feature snapshots.
- **Administrator dashboard and risk views** for cohort summaries and follow-up.
- **Student self-service portal** for viewing a student's own profile and prediction.
- **CSV bulk upload**, chatbot support, and REST API.
- **SQLite Demo Mode** that runs without XAMPP/MySQL and seeds 30 sample student records with real predictions from the saved model.
- **MySQL configuration** for a database-backed deployment.
- **MCA-521 deliverables:** formatted report (`.docx` and `.pdf`), presentation (`.pptx`), figures, and scripts to regenerate the documents under [`report/`](report/).

## Run the demo

### Requirements

- Python 3.10 or newer
- `pip`
- A modern web browser

MySQL/XAMPP is **not required** for the demo.

### Install and start

```bash
git clone https://github.com/Vaibhav41-cmd/edupredict.git
cd edupredict
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate
```

Install dependencies and launch the zero-setup demo:

```bash
pip install -r requirements.txt
python demo.py
```

Open **http://127.0.0.1:5000/** (or `/demo/`) in a browser. The application binds to `0.0.0.0:5000` for local and preview access. On first launch, SQLite tables, an administrator, and 30 sample students are created automatically. The demo database is `database/edupredict_demo.db` and is ignored by Git.

### Demo accounts

| Role | Username | Demo password | Example |
|---|---|---|---|
| Administrator | `admin` | `Admin@1234` | Admin dashboard |
| Student, predicted PASS | `MCA2024001` | `MCA2024001` | Rahul Sharma portal |
| Student, at-risk / predicted FAIL | `MCA2024004` | `MCA2024004` | Sneha Joshi portal |

The `/demo/` and login pages also provide one-click demo access. Change seeded credentials and use a private `SECRET_KEY` before deploying beyond a local demonstration.

## Train or use the saved model

Pretrained model, scaler, and metadata files are included under `ml/saved_models/`. For a fresh training run:

```bash
python ml/train.py
```

Then launch the general application with `python run.py`. The app factory loads the configured environment from `FLASK_ENV`; `python demo.py` explicitly selects SQLite Demo Mode.

## Model and evaluation

The supplied dataset contains **2,000 records**, 11 numerical predictors, and a binary target: 1,343 PASS (67.15%) and 657 FAIL (32.85%). The recorded evaluation uses a stratified 80:20 split (1,600 training / 400 test records), feature standardization, and five-fold cross-validation.

| Classifier | Accuracy | Precision | Recall | F1 | ROC-AUC | 5-fold CV accuracy |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression (selected by ROC-AUC) | 83.50% | 86.12% | 89.96% | 88.00% | **0.9082** | 84.62% ± 1.80% |
| RBF SVM | **84.75%** | 86.62% | 91.45% | 88.97% | 0.8978 | 82.94% ± 2.13% |
| Gradient Boosting | 83.50% | 86.38% | 89.59% | 87.96% | 0.8967 | 83.44% ± 1.25% |
| Random Forest | 83.00% | 84.30% | 91.82% | 87.90% | 0.8866 | 83.56% ± 0.92% |

Logistic Regression is selected by **ROC-AUC**, although RBF SVM has the higher observed accuracy on this split. Logistic Regression's test confusion matrix is TP=242, TN=92, FP=39, FN=27; its FAIL-class recall is 70.23%, so some at-risk cases are missed. Results are specific to the supplied dataset and split; external validation is needed before real institutional use.

### Model input features

Five subject marks (0–100), internal marks (0–50), attendance (0–100%), study hours per day, assignments submitted, previous backlogs, and derived average subject marks.

## Application routes

| Path | Purpose |
|---|---|
| `/` | Redirects to the live demo |
| `/demo/` | Interactive predictor, model comparison, report downloads |
| `/login` | Administrator sign-in |
| `/student/login` | Student portal sign-in |
| `/api/v1/health` | API health check |
| `/api/v1/students` | Paginated student listing |
| `/api/v1/students/<id>` | Student record lookup |
| `/api/v1/students/<id>/predict` | Re-run prediction for a student |
| `/api/v1/predict/quick` | Quick prediction without saving a student record |
| `/api/v1/model/metrics` | Model evaluation metadata |
| `/api/v1/stats/summary` | Cohort summary |
| `/demo/report/pdf` | Download the MCA-521 report PDF |
| `/demo/report/docx` | Download the editable report DOCX |
| `/demo/report/pptx` | Download the project presentation PPTX |

POST endpoints use CSRF protection in browser forms and requests.

## MySQL configuration (optional)

The default demo needs no database configuration. To configure MySQL for deployment, copy `.env.example` to `.env`, set a strong `SECRET_KEY`, and configure `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` (or an explicit `DATABASE_URL`). Create the database/schema as described in [`database/schema.sql`](database/schema.sql), then run `python run.py`. Never commit `.env` or production credentials.

## Tests

Install pytest if it is not already available, then run:

```bash
python -m pytest tests/ -v
```

The tests cover data validation, model behavior, demo seeding and prediction routes, administrator and student portal flows, report downloads, and key API/UI routes.

## Repository layout

```text
app/                 Flask factory, ORM models, route blueprints, services
frontend/            Jinja templates, CSS, and browser-side JavaScript
ml/                  Training pipeline, datasets, saved model artifacts
database/            MySQL schema and sample records
report/              MCA-521 report, presentation, figures, and generators
tests/               ML and demo integration tests
config.py            SQLite/MySQL and environment configuration
demo.py              Zero-setup SQLite demo launcher
run.py               General Flask application launcher
```

## Report and presentation

- [`EduPredict_MCA521_Project_Report.docx`](report/EduPredict_MCA521_Project_Report.docx) — editable report
- [`EduPredict_MCA521_Project_Report.pdf`](report/EduPredict_MCA521_Project_Report.pdf) — print/share copy
- [`EduPredict_MCA521_Presentation.pptx`](report/EduPredict_MCA521_Presentation.pptx) — project presentation

The report leaves student, guide, and academic-year details blank for completion. Its college logo and institutional presentation were adapted from the user-supplied previous-year report; the project research content and performance results describe this repository.
