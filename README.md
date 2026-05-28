# LearnAI: Learning Difficulty Assessment API

A Flask-powered REST API that uses a trained machine-learning model to assess students for potential learning difficulties (dyslexia, dyscalculia, memory impairment, and more), then delivers personalised resource recommendations — all accessible to students, teachers, and administrators through a role-based permission system.

---

## Features

- **ML-based assessment**: A pre-trained scikit-learn model (`best_model_real.joblib`) classifies student responses across five cognitive domains: Mathematics, Grammar, Reading, Memory, and Reasoning.
- **Role-based access**: Three roles out of the box: `student`, `teacher`, and `admin`, each with their own scoped API routes.
- **JWT authentication**: Stateless auth with 24-hour access tokens.
- **Personalised recommendations**: Auto-generated learning resources based on each student's classified difficulty profile.
- **Teacher dashboard support**: Teachers can view enrolled students, track assessment history, and receive aggregated insights.
- **Admin panel**: Full user management, question bank CRUD, and audit log access.
- **Notification system**: In-app notifications triggered by assessment events.
- **Auto-seeded database**: On first run the app seeds itself with questions and a demo admin account — no manual SQL needed.
- **SQLite by default, any SQLAlchemy DB in production**: Swap the `DATABASE_URL` env var to move to Postgres, MySQL, etc.

---

## Project Structure

```
├── app.py                  # Application factory & entry point
├── config.py               # Config class (reads from environment)
├── extensions.py           # Shared SQLAlchemy instance
├── requirements.txt        # Python dependencies
├── .env.backend.example    # Template for your .env file
│
├── models/
│   └── __init__.py         # All SQLAlchemy models (User, Assessment, Question, …)
│
├── routes/
│   ├── auth.py             # /api/auth  — register, login, profile
│   ├── assessment.py       # /api/assessment — questions, start, submit
│   ├── results.py          # /api/results — assessment history & result detail
│   ├── recommendations.py  # /api/recommendations — personalised resources
│   ├── users.py            # /api/users — student self-service
│   ├── teacher.py          # /api/teacher — teacher dashboard
│   ├── admin.py            # /api/admin — admin management
│   └── notifications.py    # /api/notifications — in-app alerts
│
├── utils/
│   ├── classifier.py       # Loads ML model & classifies assessment responses
│   ├── recommendations.py  # Generates resource recommendations from results
│   └── seed.py             # Seeds the DB with questions & demo accounts
│
└── ml_model/
    └── best_model_real.joblib  # Pre-trained scikit-learn classifier
```

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- `pip` (comes with Python)
- *(Optional)* `virtualenv` or Python's built-in `venv`

### 1. Clone the repository

```bash
git clone https://github.com/your-username/learnai-backend.git
cd learnai-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example env file and edit it:

```bash
cp .env.backend.example .env
```

Open `.env` and update the values:

```env
# Generate secure secrets with:
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Database connection string (SQLite is fine for local dev)
DATABASE_URL=sqlite:///learnai.db

# Code students/teachers use to self-register as a teacher
TEACHER_CODE=TEACHER2024

# Set to false in production to disable admin self-registration
ALLOW_ADMIN_SELF_REGISTER=true
```

### 5. Run the development server

```bash
python app.py
```

The API will start on **http://localhost:5000**. On first launch, the database tables are created and seeded automatically — no migration commands needed.

---

## Default Demo Accounts

After the first run the seed script creates the following accounts (development only — change passwords in production):

| Role    | Email                   | Password      |
|---------|-------------------------|---------------|
| Admin   | `admin@learnai.com`     | `admin123`    |
| Teacher | `teacher@learnai.com`   | `teacher123`  |
| Student | `student@learnai.com`   | `student123`  |

> **Security note:** Change all default credentials and set `ALLOW_ADMIN_SELF_REGISTER=false` before deploying to production.

---

## 📡 API Overview

All routes are prefixed with `/api`. Protected routes require a `Bearer <token>` header obtained from `/api/auth/login`.

| Prefix                  | Description                              | Access         |
|-------------------------|------------------------------------------|----------------|
| `/api/auth`             | Register, login, refresh, profile        | Public / Any   |
| `/api/assessment`       | Fetch questions, start & submit sessions | Student        |
| `/api/results`          | View past results and detailed breakdowns| Student        |
| `/api/recommendations`  | Personalised learning resource feeds     | Student        |
| `/api/users`            | Update profile, preferences, password    | Student        |
| `/api/teacher`          | Enrolled students, their assessments     | Teacher        |
| `/api/admin`            | User management, question bank, logs     | Admin          |
| `/api/notifications`    | Read and dismiss in-app notifications    | Any (auth)     |

---

## How the ML Classification Works

When a student submits an assessment:

1. Each answer is recorded with the domain, correctness, time taken, and error type.
2. `utils/classifier.py` builds a feature vector covering per-domain accuracy, response times, and error-type distributions.
3. The pre-trained model (`ml_model/best_model_real.joblib`) predicts one of six classes:

   | Model label          | Displayed as                     |
   |----------------------|----------------------------------|
   | `no_difficulty`      | No significant difficulty        |
   | `dyscalculia`        | Dyscalculia-related              |
   | `dyslexia`           | Dyslexia-related                 |
   | `memory_impairment`  | Memory-related                   |
   | `reasoning_deficit`  | Reasoning-related                |
   | `language_disorder`  | Dyslexia-related *(mapped)*      |

4. Results and a tailored recommendation set are persisted and returned to the client.

---

## ⚙️ Configuration Reference

All configuration is driven by environment variables (see `config.py`):

| Variable                   | Default                          | Description                                    |
|----------------------------|----------------------------------|------------------------------------------------|
| `SECRET_KEY`               | `dev-secret-change-in-production`| Flask secret key                               |
| `JWT_SECRET_KEY`           | `jwt-secret-change-in-production`| JWT signing key                                |
| `DATABASE_URL`             | `sqlite:///learnai.db`           | SQLAlchemy connection string                   |
| `TEACHER_CODE`             | `TEACHER2024`                    | Registration code for teacher sign-up          |
| `ALLOW_ADMIN_SELF_REGISTER`| `true`                           | Allow admin self-registration via public route |

---

## 🛠 Tech Stack

| Layer         | Technology                                  |
|---------------|---------------------------------------------|
| Framework     | Flask 3+                                    |
| ORM           | Flask-SQLAlchemy                            |
| Auth          | Flask-JWT-Extended                          |
| CORS          | Flask-CORS                                  |
| ML            | scikit-learn, NumPy, joblib                 |
| Password hash | bcrypt                                      |
| Database      | SQLite (dev) / any SQLAlchemy-supported DB  |

---

## Production Checklist

- [ ] Generate new `SECRET_KEY` and `JWT_SECRET_KEY` values
- [ ] Set `DATABASE_URL` to a production-grade database (e.g. PostgreSQL)
- [ ] Set `ALLOW_ADMIN_SELF_REGISTER=false`
- [ ] Change the `TEACHER_CODE` to a secret value
- [ ] Delete or disable demo seed accounts
- [ ] Run behind a WSGI server (e.g. Gunicorn): `gunicorn "app:create_app()"`
- [ ] Put a reverse proxy (Nginx / Caddy) in front for HTTPS

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push the branch: `git push origin feat/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
