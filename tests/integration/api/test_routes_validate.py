import pytest
from httpx import ASGITransport, AsyncClient

from app import agent
from app.agent.validator import AgentResult
from app.api import routes
from app.db.session import get_session
from app.main import app
from app.services import validation_log


@pytest.fixture(autouse=True)
def override_session_dependency():
    class DummySession:
        def add(self, *_args, **_kwargs):
            return None

        async def commit(self):
            return None

    async def _override():
        yield DummySession()

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture(autouse=True)
def stub_log(monkeypatch):
    async def _noop(session, field_type, value, result):
        return None

    monkeypatch.setattr(validation_log, "log_validation", _noop)


@pytest.fixture
def stub_agent(monkeypatch):
    async def _fake_agent(field_type, value, context=None):
        supported = {"text", "email", "phone", "number", "select", "valid1", "valid2", "valid3"}
        if field_type not in supported:
            return AgentResult(status="objection", message="unsupported")

        if field_type == "valid1":
            return AgentResult(status="success" if value.isdigit() else "objection", message="ok")

        if field_type == "valid2":
            return AgentResult(status="success" if value and value[0].isalpha() else "objection", message="ok")

        if field_type == "valid3":
            val = value.lower()
            if "dent" in val:
                return AgentResult(status="success", message="dentist")
            if "fryz" in val:
                return AgentResult(status="success", message="hairdresser")
            return AgentResult(status="objection", message="other")

        status = "success" if value else "objection"
        message = "ok" if status == "success" else "value missing"
        return AgentResult(status=status, message=message)

    monkeypatch.setattr(agent.validator, "run_validation_agent", _fake_agent)
    monkeypatch.setattr(routes, "run_validation_agent", _fake_agent)


@pytest.mark.asyncio
async def test_validate_success(stub_agent):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/validate", json={"field_type": "text", "value": "Acme"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["message"]


@pytest.mark.asyncio
async def test_validate_objection(stub_agent):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/validate", json={"field_type": "text", "value": ""})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "objection"
    assert "value" in body["message"]


@pytest.mark.asyncio
async def test_validate_unsupported_type(stub_agent):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/validate", json={"field_type": "unknown", "value": "v"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "objection"


@pytest.mark.asyncio
async def test_validate_valid1(stub_agent):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/validate", json={"field_type": "valid1", "value": "12345678901"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


@pytest.mark.asyncio
async def test_validate_valid2(stub_agent):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/validate", json={"field_type": "valid2", "value": "Warszawa"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


@pytest.mark.asyncio
async def test_validate_valid3(stub_agent):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/validate", json={"field_type": "valid3", "value": "Gabinet dentystyczny"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


@pytest.mark.asyncio
async def test_validate_valid3_hairdresser(stub_agent):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/validate", json={"field_type": "valid3", "value": "Salon fryzjerski"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


@pytest.mark.asyncio
async def test_validate_valid3_other(stub_agent):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/validate", json={"field_type": "valid3", "value": "Kucharz w restauracji"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "objection"


