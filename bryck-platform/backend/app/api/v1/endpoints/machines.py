import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
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
from app.services.machine_service import MachineService
from app.models.machine import HealthStatus, MachineStatus, MachineType, UsageType

router = APIRouter(prefix="/machines", tags=["Machines"])


# ──────────────────────────────────────────────
# Dependency factory — keeps endpoints clean
# ──────────────────────────────────────────────

def get_machine_service(
    session: AsyncSession = Depends(get_db_session),
) -> MachineService:
    return MachineService(
        repository=MachineRepository(session),
        bryck_client=BryckAPIClient(),
    )


ServiceDep = Annotated[MachineService, Depends(get_machine_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@router.get(
    "",
    response_model=MachineListResponse,
    summary="List machines with optional filters and pagination",
)
async def list_machines(
    service: ServiceDep,
    settings: SettingsDep,
    status: Optional[MachineStatus] = Query(default=None),
    used_for: Optional[UsageType] = Query(default=None),
    machine_type: Optional[MachineType] = Query(default=None),
    allotted_to: Optional[str] = Query(default=None),
    health_status: Optional[HealthStatus] = Query(default=None),
    search: Optional[str] = Query(default=None, description="Full-text search on IP, build, notes"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=None),
):
    effective_page_size = page_size or settings.DEFAULT_PAGE_SIZE
    effective_page_size = min(effective_page_size, settings.MAX_PAGE_SIZE)

    filters = MachineFilters(
        status=status,
        used_for=used_for,
        machine_type=machine_type,
        allotted_to=allotted_to,
        health_status=health_status,
        search=search,
    )
    return await service.list_machines(filters, page, effective_page_size)


@router.post(
    "",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new machine",
)
async def create_machine(
    payload: MachineCreate,
    service: ServiceDep,
):
    return await service.create_machine(payload)


@router.get(
    "/{machine_id}",
    response_model=MachineResponse,
    summary="Get a single machine by ID",
)
async def get_machine(
    machine_id: uuid.UUID,
    service: ServiceDep,
):
    return await service.get_machine(machine_id)


@router.patch(
    "/{machine_id}",
    response_model=MachineResponse,
    summary="Partially update a machine",
)
async def update_machine(
    machine_id: uuid.UUID,
    payload: MachineUpdate,
    service: ServiceDep,
):
    return await service.update_machine(machine_id, payload)


@router.delete(
    "/{machine_id}",
    response_model=MachineResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft-delete (decommission) a machine",
)
async def decommission_machine(
    machine_id: uuid.UUID,
    service: ServiceDep,
):
    return await service.decommission_machine(machine_id)


@router.post(
    "/{machine_id}/health-check",
    response_model=HealthCheckResult,
    summary="Trigger a live health check for a machine",
)
async def trigger_health_check(
    machine_id: uuid.UUID,
    service: ServiceDep,
):
    return await service.trigger_health_check(machine_id)
