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
        if field_type not in {"text", "email", "phone", "number", "select"}:
            return AgentResult(status="objection", message="unsupported")
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


