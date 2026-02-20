from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import Base, engine, get_db
from models import Machine
from schemas import MachineCreate, MachineUpdate, MachineOut

# Base.metadata.drop_all(bind=engine)   

TEST_SUITES = [
    "Config Shipment Test",
    "Stress Shipment Test",
    "Web Shipment Test",
    "Reboot Shipment Test",
    "Cloud Transfer Test"
]
# [test_config_shipment, test_stress_shipment, test_web_shipment, test_reboot_shipment, test_cloud_transfer_shipment]
PRIORITY_OPTIONS = [
    {"label": "High", "value": 0},
    {"label": "Medium", "value": 1},
    {"label": "Low", "value": 2},
]

Base.metadata.create_all(bind=engine)


def ensure_machine_columns() -> None:
    inspector = inspect(engine)
    if "machines" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("machines")}
    with engine.begin() as conn:
        if "ibmi_bmc" not in existing_columns:
            conn.execute(text("ALTER TABLE machines ADD COLUMN ibmi_bmc VARCHAR(45)"))
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_machines_ibmi_bmc "
                    "ON machines (ibmi_bmc)"
                )
            )
        if "test_status" not in existing_columns:
            conn.execute(text("ALTER TABLE machines ADD COLUMN test_status JSON"))
        if "priority" not in existing_columns:
            conn.execute(text("ALTER TABLE machines ADD COLUMN priority INTEGER DEFAULT 2"))
            conn.execute(text("UPDATE machines SET priority = 2 WHERE priority IS NULL"))


def normalize_test_status(test_status: Optional[dict[str, bool]]) -> Optional[dict[str, bool]]:
    if test_status is None:
        return None
    if not isinstance(test_status, dict):
        raise HTTPException(status_code=422, detail="test_status must be an object")

    normalized: dict[str, bool] = {}
    for suite, completed in test_status.items():
        if suite not in TEST_SUITES:
            raise HTTPException(status_code=422, detail=f"Unknown test suite: {suite}")
        if not isinstance(completed, bool):
            raise HTTPException(status_code=422, detail=f"test_status[{suite}] must be true/false")
        normalized[suite] = completed
    return normalized


def normalize_priority(priority: Optional[int]) -> Optional[int]:
    if priority is None:
        return None
    if priority not in {0, 1, 2}:
        raise HTTPException(status_code=422, detail="priority must be 0 (High), 1 (Medium), or 2 (Low)")
    return priority


ensure_machine_columns()

app = FastAPI(title="Bryck Inventory API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Inventory: List & Filter ──────────────────────────────────────
@app.get("/inventory", response_model=list[MachineOut])
def list_machines(
    status:       Optional[str] = Query(None),
    priority:     Optional[int] = Query(None),
    used_for:     Optional[str] = Query(None),
    machine_type: Optional[str] = Query(None),
    allotted_to:  Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    q = db.query(Machine)
    if status:       q = q.filter(Machine.status == status)
    if priority is not None:
        normalized_priority = normalize_priority(priority)
        q = q.filter(Machine.priority == normalized_priority)
    if used_for:     q = q.filter(Machine.used_for == used_for)
    if machine_type: q = q.filter(Machine.machine_type == machine_type)
    if allotted_to:  q = q.filter(Machine.allotted_to == allotted_to)
    return q.order_by(Machine.created_at.desc()).all()


# ── Inventory: Get single machine ─────────────────────────────────
@app.get("/inventory/{machine_id}", response_model=MachineOut)
def get_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


# ── Inventory: Add machine ────────────────────────────────────────
@app.post("/inventory", response_model=MachineOut, status_code=201)
def add_machine(payload: MachineCreate, db: Session = Depends(get_db)):
    existing = db.query(Machine).filter(Machine.ip_address == payload.ip_address).first()
    if existing:
        raise HTTPException(status_code=409, detail="IP already exists in inventory")
    if payload.ibmi_bmc:
        existing_bmc = db.query(Machine).filter(Machine.ibmi_bmc == payload.ibmi_bmc).first()
        if existing_bmc:
            raise HTTPException(status_code=409, detail="IBMi/BMC already exists in inventory")

    payload_data = payload.model_dump()
    payload_data["test_status"] = normalize_test_status(payload_data.get("test_status"))
    payload_data["priority"] = normalize_priority(payload_data.get("priority"))
    if payload_data["priority"] is None:
        payload_data["priority"] = 2

    machine = Machine(**payload_data)
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


# ── Inventory: Edit machine (partial update) ──────────────────────
@app.patch("/inventory/{machine_id}", response_model=MachineOut)
def edit_machine(machine_id: int, payload: MachineUpdate, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    updates = payload.model_dump(exclude_unset=True)
    if "ip_address" in updates and updates["ip_address"] and updates["ip_address"] != machine.ip_address:
        existing = db.query(Machine).filter(Machine.ip_address == updates["ip_address"]).first()
        if existing and existing.id != machine_id:
            raise HTTPException(status_code=409, detail="IP already exists in inventory")

    if "ibmi_bmc" in updates and updates["ibmi_bmc"] and updates["ibmi_bmc"] != machine.ibmi_bmc:
        existing_bmc = db.query(Machine).filter(Machine.ibmi_bmc == updates["ibmi_bmc"]).first()
        if existing_bmc and existing_bmc.id != machine_id:
            raise HTTPException(status_code=409, detail="IBMi/BMC already exists in inventory")

    if "test_status" in updates:
        updates["test_status"] = normalize_test_status(updates["test_status"])
    if "priority" in updates:
        updates["priority"] = normalize_priority(updates["priority"])
        if updates["priority"] is None:
            updates["priority"] = 2

    for field, value in updates.items():
        setattr(machine, field, value)
    machine.updated_at = datetime.now()
    db.commit()
    db.refresh(machine)
    return machine


# ── Inventory: Remove machine ─────────────────────────────────────
@app.delete("/inventory/{machine_id}", status_code=204)
def remove_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    db.delete(machine)
    db.commit()


# ── Dropdown options (for frontend selects) ───────────────────────
@app.get("/inventory/options/status")
def status_options():
    return ["Active", "Ready", "Down", "Shipped", "Idle"]

@app.get("/inventory/options/used-for")
def used_for_options():
    return ["Testing", "Development", "Customer", "Idle"]

@app.get("/inventory/options/machine-type")
def machine_type_options():
    return ["Bryck", "BryckMini"]

@app.get("/inventory/options/test-suites")
def test_suite_options():
    return TEST_SUITES

@app.get("/inventory/options/priority")
def priority_options():
    return PRIORITY_OPTIONS
