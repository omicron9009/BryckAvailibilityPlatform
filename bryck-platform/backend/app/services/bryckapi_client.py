"""
Mock BryckAPI client.
--------------------
Replace the internals of BryckAPIClient with real HTTP calls
when the actual BryckAPI becomes available. The interface stays identical.
"""

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.core.config import get_settings
from app.models.machine import HealthStatus

settings = get_settings()


@dataclass
class BryckDeviceInfo:
    is_reachable: bool
    health_status: HealthStatus
    current_build: Optional[str]
    checked_at: datetime


class BryckAPIClient:
    """
    Abstraction over the BryckAPI (or its mock).

    To swap to real: override _fetch_real() and call it in get_device_info().
    """

    def __init__(self):
        self._base_url = settings.BRYCK_API_BASE_URL

    async def get_device_info(self, ip: str) -> BryckDeviceInfo:
        """
        Returns live (or mocked) health and build info for a machine.
        In mock mode: simulates realistic random states.
        """
        try:
            return await self._fetch_real(ip)
        except Exception:
            # Fallback to mock if real API is unreachable
            return self._mock_response(ip)

    async def _fetch_real(self, ip: str) -> BryckDeviceInfo:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self._base_url}/device/{ip}/status")
            resp.raise_for_status()
            data = resp.json()
            return BryckDeviceInfo(
                is_reachable=data.get("reachable", False),
                health_status=HealthStatus(data.get("health", "Unknown")),
                current_build=data.get("build"),
                checked_at=datetime.now(timezone.utc),
            )

    @staticmethod
    def _mock_response(ip: str) -> BryckDeviceInfo:
        """
        Deterministic-ish mock based on IP hash so results are
        consistent across calls for the same machine during dev.
        """
        seed = sum(int(octet) for octet in ip.split(".") if octet.isdigit())
        reachable = seed % 5 != 0  # ~80% reachable
        statuses = [HealthStatus.HEALTHY, HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNREACHABLE]
        builds = ["v2.4.1", "v2.4.0", "v2.3.9", "v2.5.0-rc1", None]

        return BryckDeviceInfo(
            is_reachable=reachable,
            health_status=statuses[seed % len(statuses)],
            current_build=builds[seed % len(builds)] if reachable else None,
            checked_at=datetime.now(timezone.utc),
        )
