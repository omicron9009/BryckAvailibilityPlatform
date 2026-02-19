# Bryck Availability Platform

Internal dashboard to track machine availability, ownership, build status, and health for testing/development/deployment teams.

---

## Quick Start (One Command)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- **API**: http://localhost:8000/api/docs  
- **Frontend**: Open `frontend/index.html` in a browser (or serve via Nginx — see below)  
- **OpenAPI**: http://localhost:8000/api/openapi.json

---

## Architecture

```
Request → FastAPI Router
              ↓
         Service Layer  (business rules, no DB knowledge)
              ↓
       Repository Layer (only DB I/O, no business rules)
              ↓
     SQLAlchemy Async ORM
              ↓
         PostgreSQL
```

**Key decisions:**
- Async throughout (`asyncpg` + `async_sessionmaker`)
- Repository pattern: swap DB engine without touching services
- Mock BryckAPI client: replace `_fetch_real()` with real HTTP when API is ready
- Soft deletes: machines are never hard-deleted, only flagged `is_deleted=True`

---

## Project Structure

```
bryck-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # HTTP routers only (no business logic)
│   │   ├── core/               # Config, DB engine, exceptions
│   │   ├── models/             # SQLAlchemy ORM + Python enums
│   │   ├── schemas/            # Pydantic DTOs (in/out shapes)
│   │   ├── services/           # All business logic
│   │   └── repositories/       # All DB queries
│   ├── alembic/                # DB migrations
│   └── tests/                  # pytest-asyncio integration tests
├── frontend/
│   ├── js/
│   │   ├── api.js              # Fetch wrapper + error model
│   │   ├── store.js            # Reactive state store
│   │   ├── renderer.js         # DOM rendering functions
│   │   ├── events.js           # All event handlers
│   │   └── app.js              # Entry point + bootstrap
│   └── css/styles.css
├── docker-compose.yml
└── nginx/nginx.conf
```

---

## DB Schema

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | Auto-generated |
| machine_ip | VARCHAR(45) | Unique, indexed |
| machine_type | ENUM | Bryck / BryckMini / Other |
| status | ENUM | Active / Down / Ready / Shipped / Decommissioned; indexed |
| used_for | ENUM | Testing / Development / Customer / Idle; indexed |
| allotted_to | VARCHAR(255) | Nullable |
| can_run_parallel | BOOLEAN | |
| current_build | VARCHAR(255) | Nullable |
| tests_completed | INTEGER | Default 0 |
| active_issues | TEXT | Nullable |
| notes | TEXT | Nullable |
| health_status | ENUM | Healthy / Degraded / Unreachable / Unknown |
| is_reachable | BOOLEAN | |
| customer_name | VARCHAR(255) | Nullable |
| shipping_date | TIMESTAMPTZ | Nullable |
| is_deleted | BOOLEAN | Soft delete flag; indexed |
| created_at | TIMESTAMPTZ | server default |
| updated_at | TIMESTAMPTZ | auto-updated |

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/v1/machines | List with filters + pagination |
| POST | /api/v1/machines | Create machine |
| GET | /api/v1/machines/{id} | Get single machine |
| PATCH | /api/v1/machines/{id} | Partial update |
| DELETE | /api/v1/machines/{id} | Soft delete (decommission) |
| POST | /api/v1/machines/{id}/health-check | Trigger health + build fetch |
| GET | /health | Liveness probe |

**Filter params** (all optional): `status`, `used_for`, `machine_type`, `allotted_to`, `health_status`, `search`, `page`, `page_size`

---

## Local Dev (No Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # set DATABASE_URL to local PG

alembic upgrade head
uvicorn app.main:app --reload
```

For frontend: just open `frontend/index.html` directly. No build step.

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

Requires a running test PostgreSQL instance. Set `TEST_DB_URL` in `conftest.py` or use `DATABASE_URL` in `.env`.

---

## Adding Nginx Frontend Serving

Uncomment the `frontend` service in `docker-compose.yml`. It mounts the `frontend/` directory and proxies `/api/` to the backend.

---

## Replacing the Mock BryckAPI

In `backend/app/services/bryckapi_client.py`, update `_fetch_real()` to match the real API's response format. Set `BRYCK_API_BASE_URL` in `.env`. The mock fallback stays in place until the real API is stable.

---

## Assumptions

1. Internal network only — no public-facing SSL required at app level (terminate TLS at load balancer or Nginx).
2. Auth is explicitly deferred — CORS is configured, service/repo layers are auth-agnostic, ready for JWT middleware injection.
3. `machine_ip` is the human-facing primary identifier; UUID is the canonical system key.
4. BryckAPI returns JSON `{ reachable, health, build }` — mocked accordingly.
5. Frontend is served as static files; no Node.js, no bundler required.
