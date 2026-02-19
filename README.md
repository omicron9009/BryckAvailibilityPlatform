# Bryck Availability Platform

A lightweight internal dashboard to track availability, ownership, usage,
and health of machines used for testing, development, and deployments.

---

## Tech Stack

- **Backend** — FastAPI + PostgreSQL + SQLAlchemy
- **Frontend** — Vanilla HTML, CSS, JavaScript (single file)

---

## Project Structure

BryckAvailabilityPlatform/
├── backend/
│ ├── main.py # FastAPI app + all routes
│ ├── models.py # SQLAlchemy models
│ ├── schemas.py # Pydantic schemas
│ ├── database.py # DB connection
│ ├── .env # Environment variables
│ └── requirements.txt
└── frontend/
└── index.html # Single file frontend

text

---

## Prerequisites

- Python 3.10+
- PostgreSQL installed and running

---

## Setup & Running

### 1. Create the Database

Open CMD and run:

```bash
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres
Then inside psql:

sql
CREATE DATABASE bryck_db;
\q
2. Backend Setup
bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt
3. Configure Environment
Edit .env in the backend folder:

text
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/bryck_db
4. Start the Backend
bash
uvicorn main:app --reload --port 8000
Server runs at → http://localhost:8000
Swagger docs at → http://localhost:8000/docs

5. Start the Frontend
bash
cd frontend
python -m http.server 5500
Open → http://localhost:5500

API Routes
Inventory
Method	Route	Description
GET	/inventory	List all machines (supports filters)
GET	/inventory/{machine_id}	Get a single machine by ID
POST	/inventory	Add a new machine
PATCH	/inventory/{machine_id}	Edit one or more fields on a machine
DELETE	/inventory/{machine_id}	Remove a machine
Filters (on GET /inventory)
Append as query params:

text
GET /inventory?status=Active
GET /inventory?machine_type=Bryck
GET /inventory?used_for=Testing
GET /inventory?allotted_to=TeamA
Dropdown Options
Method	Route	Returns
GET	/inventory/options/status	["Active", "Ready", "Down", "Shipped", "Idle"]
GET	/inventory/options/used-for	["Testing", "Development", "Customer", "Idle"]
GET	/inventory/options/machine-type	["Bryck", "BryckMini"]
Machine Fields
Field	Type	Description
ip_address	string	Primary identifier — must be unique
hostname	string	Machine hostname
machine_type	string	Bryck or BryckMini
status	string	Active, Ready, Down, Shipped, Idle
used_for	string	Testing, Development, Customer, Idle
allotted_to	string	Person or team name
can_parallel	boolean	Can be used in parallel — true / false
current_build	string	Build ID or tag
tests_completed	string	Number or Na
active_issues	string	Short issue summary or Na
last_health_status	string	Healthy, Degraded, Down
is_reachable	boolean	Reachable via API or SSH
reachable_via	string	API or SSH
customer	string	Customer or company name
shipping_date	date	YYYY-MM-DD format
notes	string	Free text / to-do
Example API Calls
Add a machine:

bash
curl -X POST http://localhost:8000/inventory \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "192.168.1.10", "machine_type": "Bryck", "status": "Ready"}'
Edit a field:

bash
curl -X PATCH http://localhost:8000/inventory/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "Active", "allotted_to": "Jadi"}'
Delete a machine:

bash
curl -X DELETE http://localhost:8000/inventory/1
Notes
create_all() auto-creates the table on first run — no manual SQL needed

If the table schema changes, drop the table and restart:

sql
DROP TABLE IF EXISTS machines;
All frontend dropdowns are driven by the options API — update the lists in main.py to reflect changes everywhere instantly

text
undefined