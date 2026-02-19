import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

import enum as py_enum


class MachineType(str, py_enum.Enum):
    BRYCK = "Bryck"
    BRYCK_MINI = "BryckMini"
    OTHER = "Other"


class MachineStatus(str, py_enum.Enum):
    ACTIVE = "Active"
    DOWN = "Down"
    READY = "Ready"
    SHIPPED = "Shipped"
    DECOMMISSIONED = "Decommissioned"


class UsageType(str, py_enum.Enum):
    TESTING = "Testing"
    DEVELOPMENT = "Development"
    CUSTOMER = "Customer"
    IDLE = "Idle"


class HealthStatus(str, py_enum.Enum):
    HEALTHY = "Healthy"
    DEGRADED = "Degraded"
    UNREACHABLE = "Unreachable"
    UNKNOWN = "Unknown"


class Machine(Base):
    __tablename__ = "machines"

    # Identity
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    machine_ip: Mapped[str] = mapped_column(
        String(45),  # supports IPv6
        nullable=False,
        unique=True,
        index=True,
    )
    machine_type: Mapped[MachineType] = mapped_column(
        Enum(MachineType, name="machine_type_enum"),
        nullable=False,
        default=MachineType.BRYCK,
    )
    status: Mapped[MachineStatus] = mapped_column(
        Enum(MachineStatus, name="machine_status_enum"),
        nullable=False,
        default=MachineStatus.READY,
        index=True,
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Usage
    used_for: Mapped[UsageType] = mapped_column(
        Enum(UsageType, name="usage_type_enum"),
        nullable=False,
        default=UsageType.IDLE,
        index=True,
    )
    allotted_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    can_run_parallel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Operational
    current_build: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tests_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Health
    health_status: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus, name="health_status_enum"),
        nullable=False,
        default=HealthStatus.UNKNOWN,
    )
    is_reachable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Customer
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_machines_status_deleted", "status", "is_deleted"),
        Index("ix_machines_used_for_deleted", "used_for", "is_deleted"),
    )

    def __repr__(self) -> str:
        return f"<Machine id={self.id} ip={self.machine_ip} status={self.status}>"
