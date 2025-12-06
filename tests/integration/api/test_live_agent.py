import os

import httpx
import pytest
import pytest_asyncio

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest_asyncio.fixture(scope="function")
async def live_client():
    if os.getenv("RUN_LIVE_API") != "1":
        pytest.skip("Set RUN_LIVE_API=1 to run live API tests.")

    client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=5)
    try:
        resp = await client.get("/health")
        if resp.status_code >= 400:
            pytest.skip(f"Health check failed: {resp.status_code}")
    except Exception as exc:  # noqa: BLE001
        await client.aclose()
        pytest.skip(f"Health check failed: {exc}")

    try:
        yield client
    finally:
        await client.aclose()


@pytest.mark.live_api
@pytest.mark.asyncio
async def test_live_text_success(live_client: httpx.AsyncClient):
    resp = await live_client.post(
        "/api/validate",
        json={"field_type": "text", "value": "Acme Corporation", "context": "Company name"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["justification"]


@pytest.mark.live_api
@pytest.mark.asyncio
async def test_live_email_invalid(live_client: httpx.AsyncClient):
    resp = await live_client.post(
        "/api/validate",
        json={"field_type": "email", "value": "not-an-email", "context": "Contact email"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "objection"
    assert body["justification"]


@pytest.mark.live_api
@pytest.mark.asyncio
async def test_live_phone_invalid(live_client: httpx.AsyncClient):
    resp = await live_client.post(
        "/api/validate",
        json={"field_type": "phone", "value": "abc123", "context": "Phone number"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "objection"
    assert body["justification"]


