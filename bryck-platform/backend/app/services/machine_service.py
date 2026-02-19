import math
import uuid
from datetime import datetime, timezone

from app.core.exceptions import (
    MachineAlreadyDecommissionedError,
    MachineIPConflictError,
    MachineNotFoundError,
)
from app.models.machine import MachineStatus
from app.repositories.machine_repository import MachineRepository
from app.schemas.machine import (
    HealthCheckResult,
    MachineCreate,
    MachineFilters,
    MachineListResponse,
    MachineResponse,
    MachineUpdate,
)
from app.services.bryckapi_client import BryckAPIClient


class MachineService:
    """
    Owns all business rules for the Machine aggregate.
    Repository and external client injected — never instantiated here.
    """

    def __init__(
        self,
        repository: MachineRepository,
        bryck_client: BryckAPIClient,
    ):
        self._repo = repository
        self._bryck = bryck_client

    # ──────────────────────────────────────────────
    # Queries
    # ──────────────────────────────────────────────

    async def get_machine(self, machine_id: uuid.UUID) -> MachineResponse:
        machine = await self._repo.get_by_id(machine_id)
        if not machine:
            raise MachineNotFoundError(str(machine_id))
        return MachineResponse.model_validate(machine)

    async def list_machines(
        self,
        filters: MachineFilters,
        page: int,
        page_size: int,
    ) -> MachineListResponse:
        machines, total = await self._repo.list_machines(filters, page, page_size)
        pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
        return MachineListResponse(
            items=[MachineResponse.model_validate(m) for m in machines],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    # ──────────────────────────────────────────────
    # Commands
    # ──────────────────────────────────────────────

    async def create_machine(self, data: MachineCreate) -> MachineResponse:
        existing = await self._repo.get_by_ip(data.machine_ip)
        if existing:
            raise MachineIPConflictError(data.machine_ip)
        machine = await self._repo.create(data)
        return MachineResponse.model_validate(machine)

    async def update_machine(
        self, machine_id: uuid.UUID, data: MachineUpdate
    ) -> MachineResponse:
        machine = await self._repo.get_by_id(machine_id)
        if not machine:
            raise MachineNotFoundError(str(machine_id))
        machine = await self._repo.update(machine, data)
        return MachineResponse.model_validate(machine)

    async def decommission_machine(self, machine_id: uuid.UUID) -> MachineResponse:
        machine = await self._repo.get_by_id(machine_id)
        if not machine:
            raise MachineNotFoundError(str(machine_id))
        if machine.status == MachineStatus.DECOMMISSIONED:
            raise MachineAlreadyDecommissionedError(str(machine_id))
        machine = await self._repo.soft_delete(machine)
        return MachineResponse.model_validate(machine)

    async def trigger_health_check(self, machine_id: uuid.UUID) -> HealthCheckResult:
        machine = await self._repo.get_by_id(machine_id)
        if not machine:
            raise MachineNotFoundError(str(machine_id))

        info = await self._bryck.get_device_info(machine.machine_ip)

        machine = await self._repo.update_health(
            machine=machine,
            is_reachable=info.is_reachable,
            health_status=info.health_status,
            current_build=info.current_build,
        )

        return HealthCheckResult(
            machine_id=machine.id,
            machine_ip=machine.machine_ip,
            is_reachable=info.is_reachable,
            health_status=info.health_status,
            current_build=info.current_build,
            checked_at=info.checked_at,
        )
