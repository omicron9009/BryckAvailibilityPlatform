import math
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple, List

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import Machine, MachineStatus
from app.schemas.machine import MachineCreate, MachineFilters, MachineUpdate


class MachineRepository:
    """
    Single source of truth for all DB access on the Machine aggregate.
    No business logic lives here — only persistence mechanics.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    # ──────────────────────────────────────────────
    # Queries
    # ──────────────────────────────────────────────

    async def get_by_id(self, machine_id: uuid.UUID) -> Optional[Machine]:
        result = await self._session.execute(
            select(Machine).where(
                Machine.id == machine_id,
                Machine.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_ip(self, ip: str) -> Optional[Machine]:
        result = await self._session.execute(
            select(Machine).where(
                Machine.machine_ip == ip,
                Machine.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_machines(
        self,
        filters: MachineFilters,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Machine], int]:
        query = select(Machine).where(Machine.is_deleted.is_(False))

        if filters.status:
            query = query.where(Machine.status == filters.status)
        if filters.used_for:
            query = query.where(Machine.used_for == filters.used_for)
        if filters.machine_type:
            query = query.where(Machine.machine_type == filters.machine_type)
        if filters.allotted_to:
            query = query.where(Machine.allotted_to.ilike(f"%{filters.allotted_to}%"))
        if filters.health_status:
            query = query.where(Machine.health_status == filters.health_status)
        if filters.search:
            term = f"%{filters.search}%"
            query = query.where(
                Machine.machine_ip.ilike(term)
                | Machine.notes.ilike(term)
                | Machine.current_build.ilike(term)
                | Machine.allotted_to.ilike(term)
            )

        # Total count (same filters, no pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(Machine.created_at.desc()).offset(offset).limit(page_size)

        result = await self._session.execute(query)
        machines = list(result.scalars().all())

        return machines, total

    # ──────────────────────────────────────────────
    # Mutations
    # ──────────────────────────────────────────────

    async def create(self, data: MachineCreate) -> Machine:
        machine = Machine(**data.model_dump())
        self._session.add(machine)
        await self._session.flush()  # get PK without committing
        await self._session.refresh(machine)
        return machine

    async def update(self, machine: Machine, data: MachineUpdate) -> Machine:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(machine, field, value)
        machine.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(machine)
        return machine

    async def soft_delete(self, machine: Machine) -> Machine:
        machine.is_deleted = True
        machine.status = MachineStatus.DECOMMISSIONED
        machine.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return machine

    async def update_health(
        self,
        machine: Machine,
        is_reachable: bool,
        health_status,
        current_build: Optional[str],
    ) -> Machine:
        machine.is_reachable = is_reachable
        machine.health_status = health_status
        machine.current_build = current_build
        machine.last_checked_at = datetime.now(timezone.utc)
        machine.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(machine)
        return machine
