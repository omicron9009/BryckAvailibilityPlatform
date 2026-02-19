from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import Base, engine, get_db
from models import Machine
from schemas import MachineCreate, MachineUpdate, MachineOut

# Base.metadata.drop_all(bind=engine)   

Base.metadata.create_all(bind=engine)

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
    used_for:     Optional[str] = Query(None),
    machine_type: Optional[str] = Query(None),
    allotted_to:  Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    q = db.query(Machine)
    if status:       q = q.filter(Machine.status == status)
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
    machine = Machine(**payload.model_dump())
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
