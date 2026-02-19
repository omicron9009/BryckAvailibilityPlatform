import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator
import re

from app.models.machine import HealthStatus, MachineStatus, MachineType, UsageType


# ──────────────────────────────────────────────
# Shared validators
# ──────────────────────────────────────────────

_IP_RE = re.compile(
    r"^(\d{1,3}\.){3}\d{1,3}$"  # IPv4 simple check
    r"|^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"  # IPv6
)


class _MachineBase(BaseModel):
    machine_ip: str = Field(..., max_length=45, description="IPv4 or IPv6 address")
    machine_type: MachineType = Field(default=MachineType.BRYCK)
    status: MachineStatus = Field(default=MachineStatus.READY)
    used_for: UsageType = Field(default=UsageType.IDLE)
    allotted_to: Optional[str] = Field(default=None, max_length=255)
    can_run_parallel: bool = Field(default=False)
    current_build: Optional[str] = Field(default=None, max_length=255)
    tests_completed: int = Field(default=0, ge=0)
    active_issues: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN)
    is_reachable: bool = Field(default=False)
    customer_name: Optional[str] = Field(default=None, max_length=255)
    shipping_date: Optional[datetime] = Field(default=None)

    @field_validator("machine_ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        v = v.strip()
        if not _IP_RE.match(v):
            raise ValueError(f"'{v}' is not a valid IPv4 or IPv6 address.")
        return v


# ──────────────────────────────────────────────
# Request schemas
# ──────────────────────────────────────────────

class MachineCreate(_MachineBase):
    pass


class MachineUpdate(BaseModel):
    """All fields optional for partial updates (PATCH semantics)."""
    machine_type: Optional[MachineType] = None
    status: Optional[MachineStatus] = None
    used_for: Optional[UsageType] = None
    allotted_to: Optional[str] = Field(default=None, max_length=255)
    can_run_parallel: Optional[bool] = None
    current_build: Optional[str] = Field(default=None, max_length=255)
    tests_completed: Optional[int] = Field(default=None, ge=0)
    active_issues: Optional[str] = None
    notes: Optional[str] = None
    health_status: Optional[HealthStatus] = None
    is_reachable: Optional[bool] = None
    customer_name: Optional[str] = Field(default=None, max_length=255)
    shipping_date: Optional[datetime] = None


# ──────────────────────────────────────────────
# Response schemas
# ──────────────────────────────────────────────

class MachineResponse(_MachineBase):
    id: uuid.UUID
    last_checked_at: Optional[datetime]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MachineListResponse(BaseModel):
    items: List[MachineResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ──────────────────────────────────────────────
# Health check result
# ──────────────────────────────────────────────

class HealthCheckResult(BaseModel):
    machine_id: uuid.UUID
    machine_ip: str
    is_reachable: bool
    health_status: HealthStatus
    current_build: Optional[str]
    checked_at: datetime


# ──────────────────────────────────────────────
# Filter schema
# ──────────────────────────────────────────────

class MachineFilters(BaseModel):
    status: Optional[MachineStatus] = None
    used_for: Optional[UsageType] = None
    machine_type: Optional[MachineType] = None
    allotted_to: Optional[str] = None
    health_status: Optional[HealthStatus] = None
    search: Optional[str] = Field(default=None, description="Search in IP, notes, build")
