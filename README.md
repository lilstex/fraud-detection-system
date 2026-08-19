# Real-Time Machine Learning Fraud Detection System for Nigerian Mobile Money

A working prototype that scores mobile money transactions in real time using
machine learning, with **Nigerian-context feature engineering** and
**SHAP-based analyst explainability**.

This is the reference implementation for the MIT Professional Master's Project
at MIVA Open University: _"Real-Time Machine Learning Fraud Detection System for
Mobile Money Transactions with Nigerian-Context Feature Adaptation."_

---

## What it does

- Accepts mobile money transactions through a REST API.
- Applies **fourteen Nigerian-context engineered features** covering the seven
  fraud patterns most commonly reported by NIBSS: agent density, SIM-swap risk,
  multiple-beneficiary transfers, USSD behaviour, cash-out clustering,
  device-change frequency, and geographic anomalies.
- Scores each transaction with a trained **XGBoost model** (trained with SMOTE
  on ~60,000 synthetic transactions).
- Produces **per-transaction SHAP explanations** so a fraud analyst can see
  which features drove the decision.
- Presents everything through a **React dashboard** that reproduces the
  screens documented in Chapters 4 and 5 of the report.
- Includes a **rule-based baseline** for the Chapter 5 comparison.

---

## Screens

| Screen                     | File                                    |
| -------------------------- | --------------------------------------- |
| Login                      | `frontend/src/pages/Login.jsx`          |
| Dashboard home             | `frontend/src/pages/Dashboard.jsx`      |
| New transaction submission | `frontend/src/pages/NewTransaction.jsx` |
| Scoring result + SHAP      | `frontend/src/pages/Result.jsx`         |
| Alerts (filterable)        | `frontend/src/pages/Alerts.jsx`         |
| Transaction history        | `frontend/src/pages/History.jsx`        |
| Reports                    | `frontend/src/pages/Reports.jsx`        |
| Settings                   | `frontend/src/pages/Settings.jsx`       |

---

## Architecture

```
┌────────────────┐     REST/JSON     ┌───────────────────────────┐
│  React + Vite  │◄──────────────────►│  FastAPI (Python)         │
│  Tailwind CSS  │                    │  ├── Feature engineering   │
│                │                    │  ├── XGBoost model + SHAP  │
│                │                    │  ├── Rule-based baseline   │
│                │                    │  └── SQLAlchemy → SQLite   │
└────────────────┘                    └───────────────────────────┘
```

Backend layers map exactly to the ER diagram in Chapter 4:
`transactions` 1:1 `features`, `transactions` 1:1 `predictions`, `predictions`
1:0..1 `reviews`.

---

## Prerequisites

- **Python 3.10 or newer**
- **Node.js 18 or newer** (with `npm`)
- **Git** (optional, for cloning)

---

## Quick start (local, without Docker)

### 1. Backend

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate

# Install dependencies (this may take a couple of minutes for XGBoost + SHAP)
pip install -r requirements.txt

# Generate synthetic training data (~60,000 rows)
python scripts/generate_synthetic_data.py

# Train the three models and save artefacts
python scripts/train_models.py

# Seed the SQLite database with 12 sample scored transactions
python scripts/seed_database.py

# Start the API
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` and its interactive Swagger docs
are at `http://localhost:8000/docs`.

### 2. Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The dashboard is now at `http://localhost:3000`. Sign in with the demo
credentials:

- Analyst: `analyst / analyst123`
- Admin: `admin / admin123`

---

## Quick start (local, with Docker)

If you have Docker and `docker compose` installed, one command builds and
starts everything:

```bash
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

The first start-up takes 3–5 minutes because the backend container generates
data, trains the models, and seeds the database as part of its bootstrap.
Subsequent starts are instant because the artefacts are cached in Docker
volumes.

---

## Deploying to a VPS or Render

See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions covering:

- Render (free tier, easiest option, one-click via `render.yaml`)
- A Linux VPS (Ubuntu 22.04) with Docker Compose
- Environment variables, HTTPS, and PostgreSQL migration notes.

---

## Endpoints

| Method | Path                  | Purpose                                 | Auth  |
| ------ | --------------------- | --------------------------------------- | ----- |
| `GET`  | `/health`             | Health check                            | No    |
| `POST` | `/auth/login`         | Get JWT token                           | No    |
| `POST` | `/predict`            | Score a transaction (returns SHAP)      | Yes   |
| `POST` | `/compare`            | Return both ML and rule-based decisions | Yes   |
| `GET`  | `/transactions`       | List scored transactions with filters   | Yes   |
| `GET`  | `/transactions/{id}`  | Full detail incl. SHAP + review status  | Yes   |
| `POST` | `/reviews`            | Record analyst review decision          | Yes   |
| `GET`  | `/stats`              | Dashboard summary                       | Yes   |
| `GET`  | `/alerts/recent`      | Recent alerts for the home widget       | Yes   |
| `POST` | `/admin/model/reload` | Reload model artefacts from disk        | Admin |

Full request/response shapes are in the Swagger UI at `/docs`.

---

## Sample transactions

`backend/data/sample_transactions.json` contains 12 hand-crafted transactions
demonstrating each of the seven Nigerian fraud patterns plus legitimate
counter-examples. The seed script loads them so the dashboard has data on
first launch.

You can also try the built-in **Load fraud sample** / **Load legitimate
sample** buttons on the _New Transaction_ screen.

---

## Project structure

```
fraud-detection-system/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── config.py             # Settings
│   │   ├── database.py           # SQLAlchemy setup
│   │   ├── models.py             # ORM models (Transactions, Features, Predictions, Reviews)
│   │   ├── schemas.py            # Pydantic request/response schemas
│   │   ├── auth.py               # JWT auth
│   │   ├── ml/
│   │   │   ├── feature_engineering.py   # 14 Nigerian-context features
│   │   │   ├── model_service.py         # Model + SHAP singleton
│   │   │   └── rule_based.py            # Chapter 5 baseline
│   │   └── routers/              # One file per endpoint group
│   ├── scripts/
│   │   ├── generate_synthetic_data.py   # PaySim-style data + Nigerian metadata
│   │   ├── train_models.py              # LR + RF + XGBoost + SMOTE + SHAP
│   │   ├── seed_database.py             # Load sample_transactions.json
│   │   └── bootstrap.py                 # Idempotent container bootstrap
│   ├── data/
│   │   ├── sample_transactions.json     # 12 samples (5 fraud + 7 legitimate)
│   │   └── synthetic_transactions.csv   # Generated (not in git)
│   ├── models/                   # Generated model artefacts (not in git)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Router
│   │   ├── main.jsx              # Entry point
│   │   ├── index.css             # Tailwind base
│   │   ├── components/           # Sidebar, StatCard, ShapBarChart, Layout
│   │   ├── pages/                # Login, Dashboard, NewTransaction, Result, Alerts, History, Reports, Settings
│   │   └── utils/                # api.js, auth.jsx, format.js
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── render.yaml                   # Render one-click blueprint
├── .env.example
├── DEPLOYMENT.md
└── README.md
```

---

## Retraining the model with your own data

If you have real (anonymised) transaction data in the same schema as
`data/synthetic_transactions.csv`, replace that file and re-run
`python scripts/train_models.py`. The training script and the inference-time
feature engineering share the same code, so retraining does not require
any application code changes.

---

## Limitations

Consistent with the disclosures in Chapter 6 of the report:

1. The prototype is trained on synthetic data augmented with Nigerian
   metadata calibrated to published NIBSS patterns - not on real Nigerian
   mobile money transactions.
2. Authentication is JWT-based but uses hardcoded demo credentials. Replace
   with a real users table before any production use.
3. The prototype uses REST rather than a streaming pipeline (Kafka/Spark
   Streaming). See Section 2.3.8 of the report for the migration path.
4. Deployment security (HTTPS, secrets management, rate limiting, audit
   logging) is not part of the prototype.

---

## Licence

Academic project, MIT Open University Nigeria, Professional Master's programme.

---

## Author

**Emmanuel Mbagwu**, MIT, Miva Open University Abuja.
Supervisor: Dr. Theresa Ojowumi.
