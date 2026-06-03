# 💰 Expense Tracker API

A production-ready REST API for tracking personal expenses, built with **FastAPI**, **SQLAlchemy**, and **JWT authentication**.

## ✨ Features

- **User Authentication** — Register, login, and JWT-based session management
- **Expense CRUD** — Create, read, update, and delete personal expenses
- **Smart Filtering** — Filter by category, date range, amount range, and keyword search
- **Analytics** — Expense summaries, category breakdowns, and monthly reports
- **Pagination** — Efficient paginated listing of expenses
- **Rate Limiting** — Protect endpoints from abuse
- **Docker Ready** — Containerized deployment with PostgreSQL
- **API Docs** — Auto-generated Swagger UI and ReDoc documentation

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | Programming Language |
| FastAPI | Web Framework |
| SQLAlchemy | ORM |
| SQLite / PostgreSQL | Database |
| Alembic | Database Migrations |
| JWT (python-jose) | Authentication |
| Passlib + bcrypt | Password Hashing |
| Pydantic | Data Validation |
| Uvicorn | ASGI Server |
| Docker | Containerization |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/expense-tracker-api.git
cd expense-tracker-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 📖 API Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# The API will be available at http://localhost:8000
# PostgreSQL will be available at localhost:5432
```

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/users/register` | Register a new user | ❌ |
| POST | `/users/login` | Login and get JWT token | ❌ |
| GET | `/users/me` | Get current user profile | ✅ |

### Expenses

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/expenses` | Create a new expense | ✅ |
| GET | `/expenses` | List expenses (filtered) | ✅ |
| GET | `/expenses/{id}` | Get expense by ID | ✅ |
| PUT | `/expenses/{id}` | Update an expense | ✅ |
| DELETE | `/expenses/{id}` | Delete an expense | ✅ |

### Analytics

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/expenses/summary` | Total spending summary | ✅ |
| GET | `/expenses/category-summary` | Breakdown by category | ✅ |
| GET | `/expenses/monthly-report` | Monthly spending report | ✅ |

### Filtering Parameters

| Parameter | Type | Description |
|---|---|---|
| `category` | string | Filter by expense category |
| `month` | int (1-12) | Filter by month |
| `year` | int | Filter by year |
| `min_amount` | float | Minimum amount filter |
| `max_amount` | float | Maximum amount filter |
| `search` | string | Search in title/description |
| `page` | int | Page number (default: 1) |
| `limit` | int | Items per page (default: 10) |

## 🗄️ Database Migrations (Alembic)

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## 📁 Project Structure

```
expense_tracker_api/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app entry point
│   ├── database.py        # Database engine & session
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic validation schemas
│   ├── auth.py            # JWT authentication logic
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── user.py        # User registration & login
│   │   └── expense.py     # Expense CRUD & analytics
│   └── utils/
│       ├── __init__.py
│       ├── config.py       # App configuration
│       └── hashing.py      # Password hashing utilities
├── alembic/               # Database migrations
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
├── .gitignore
└── README.md
```

## 🔐 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./expense_tracker.db` | Database connection string |
| `SECRET_KEY` | — | JWT signing secret (required) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiry in minutes |
| `RATE_LIMIT_PER_MINUTE` | `100` | General rate limit |
| `AUTH_RATE_LIMIT_PER_MINUTE` | `10` | Auth endpoint rate limit |

## 📝 License

This project is open source and available under the [MIT License](LICENSE).
