import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_machine(client: AsyncClient):
    payload = {
        "machine_ip": "192.168.1.10",
        "machine_type": "Bryck",
        "status": "Ready",
        "used_for": "Testing",
    }
    resp = await client.post("/api/v1/machines", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["machine_ip"] == "192.168.1.10"
    assert "id" in data


@pytest.mark.asyncio
async def test_duplicate_ip_rejected(client: AsyncClient):
    payload = {"machine_ip": "192.168.1.11", "machine_type": "BryckMini", "status": "Active", "used_for": "Idle"}
    await client.post("/api/v1/machines", json=payload)
    resp = await client.post("/api/v1/machines", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_machines(client: AsyncClient):
    resp = await client.get("/api/v1/machines")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body


@pytest.mark.asyncio
async def test_filter_by_status(client: AsyncClient):
    resp = await client.get("/api/v1/machines?status=Ready")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_patch_machine(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/machines",
        json={"machine_ip": "10.0.0.5", "machine_type": "Bryck", "status": "Active", "used_for": "Development"},
    )
    mid = create_resp.json()["id"]
    patch_resp = await client.patch(f"/api/v1/machines/{mid}", json={"allotted_to": "Alice"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["allotted_to"] == "Alice"


@pytest.mark.asyncio
async def test_soft_delete(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/machines",
        json={"machine_ip": "10.0.0.99", "machine_type": "Bryck", "status": "Active", "used_for": "Idle"},
    )
    mid = create_resp.json()["id"]
    del_resp = await client.delete(f"/api/v1/machines/{mid}")
    assert del_resp.status_code == 200
    assert del_resp.json()["is_deleted"] is True
    # Confirm it's gone from list
    get_resp = await client.get(f"/api/v1/machines/{mid}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/machines",
        json={"machine_ip": "10.10.0.1", "machine_type": "Bryck", "status": "Active", "used_for": "Testing"},
    )
    mid = create_resp.json()["id"]
    hc_resp = await client.post(f"/api/v1/machines/{mid}/health-check")
    assert hc_resp.status_code == 200
    body = hc_resp.json()
    assert "health_status" in body
    assert "is_reachable" in body
