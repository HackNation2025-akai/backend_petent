import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.api import forms as forms_api
from app.api import sessions as sessions_api
from app.core import security
from app.main import app


class _StubSession:
    def __init__(self, status: str = "open"):
        self.id = uuid.uuid4()
        self.status = status
        self.form_type = "EWYP"
        self.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)


class _StubVersion:
    def __init__(self, version: int = 1, payload: dict | None = None):
        self.version = version
        self.created_at = datetime.now(timezone.utc)
        self.source = "raw"
        self.comment = None
        self.payload = payload or {}
        self.validations = []


class _StubValidation:
    def __init__(self, field_path: str, status: str, justification: str):
        self.field_path = field_path
        self.status = status
        self.justification = justification


@pytest.fixture(autouse=True)
def override_db_session():
    async def _override():
        yield None

    app.dependency_overrides[security.get_session] = _override
    yield
    app.dependency_overrides.pop(security.get_session, None)


@pytest.fixture
def stub_current_session(monkeypatch):
    stub = _StubSession()

    async def _override():
        return stub

    app.dependency_overrides[security.get_current_session] = _override
    yield stub
    app.dependency_overrides.pop(security.get_current_session, None)


@pytest.mark.asyncio
async def test_create_session(monkeypatch):
    stub = _StubSession()

    async def _fake_create_session(_db, form_type, case_ref):
        return stub, "token-123"

    monkeypatch.setattr(sessions_api, "create_session", _fake_create_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/sessions", json={"form_type": "EWYP"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_id"] == str(stub.id)
    assert data["session_token"] == "token-123"


@pytest.mark.asyncio
async def test_refresh_token(monkeypatch, stub_current_session):
    async def _fake_refresh(_db, session_id):
        return stub_current_session, "token-new"

    monkeypatch.setattr(sessions_api, "refresh_token", _fake_refresh)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/sessions/{stub_current_session.id}/refresh-token",
            headers={"Authorization": "Bearer abc"},
        )
    assert resp.status_code == 200
    assert resp.json()["session_token"] == "token-new"


@pytest.mark.asyncio
async def test_close_session(monkeypatch, stub_current_session):
    async def _fake_close(_db, session_id):
        return _StubSession(status="closed")

    monkeypatch.setattr(sessions_api, "close_session", _fake_close)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/sessions/{stub_current_session.id}/close",
            headers={"Authorization": "Bearer abc"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


@pytest.mark.asyncio
async def test_submit_form(monkeypatch, stub_current_session):
    version = _StubVersion(version=2)

    async def _fake_submit(_db, session_id, payload, source, comment):
        return version

    monkeypatch.setattr(forms_api, "submit_form", _fake_submit)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/sessions/{stub_current_session.id}/forms",
            headers={"Authorization": "Bearer abc"},
            json={"payload": {"foo": "bar"}, "source": "raw"},
        )
    assert resp.status_code == 201
    assert resp.json()["version"] == 2


@pytest.mark.asyncio
async def test_validate_form(monkeypatch, stub_current_session):
    version = _StubVersion(version=3)
    validations = [
        _StubValidation(field_path="injured_person.pesel", status="success", justification="ok"),
        _StubValidation(field_path="injured_person.last_name", status="objection", justification="bad"),
    ]

    async def _fake_validate(_db, session_id, payload, fields_to_validate):
        version.validations = validations
        return version, validations

    monkeypatch.setattr(forms_api, "validate_form", _fake_validate)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/sessions/{stub_current_session.id}/validate",
            headers={"Authorization": "Bearer abc"},
            json={"payload": {"injured_person": {"pesel": "123"}}, "fields_to_validate": None},
        )
    body = resp.json()
    assert resp.status_code == 200
    assert body["version"] == 3
    assert body["summary"]["success"] == 1
    assert body["summary"]["objection"] == 1


@pytest.mark.asyncio
async def test_history(monkeypatch, stub_current_session):
    v1 = _StubVersion(version=1)
    v2 = _StubVersion(version=2)

    async def _fake_history(_db, session_id, limit, offset):
        return 2, [v2, v1]

    monkeypatch.setattr(forms_api, "get_history", _fake_history)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/sessions/{stub_current_session.id}/history",
            headers={"Authorization": "Bearer abc"},
        )
    data = resp.json()
    assert resp.status_code == 200
    assert data["total_versions"] == 2
    assert data["versions"][0]["version"] == 2


@pytest.mark.asyncio
async def test_get_version(monkeypatch, stub_current_session):
    version = _StubVersion(version=5, payload={"foo": "bar"})
    version.validations = [
        _StubValidation(field_path="injured_person.pesel", status="success", justification="ok")
    ]

    async def _fake_get_version(_db, session_id, version_number):
        return version

    monkeypatch.setattr(forms_api, "get_version", _fake_get_version)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/sessions/{stub_current_session.id}/forms/5",
            headers={"Authorization": "Bearer abc"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == 5
    assert data["payload"]["foo"] == "bar"
    assert data["validations"][0]["status"] == "success"


@pytest.mark.asyncio
async def test_get_pdf(monkeypatch, stub_current_session):
    version = _StubVersion(
        version=1,
        payload={"injured_person": {}, "injured_address": {}, "accident_info": {}},
    )

    async def _fake_get_version(_db, session_id, version_number):
        return version

    monkeypatch.setattr(forms_api, "get_version", _fake_get_version)
    monkeypatch.setattr(forms_api, "generate_ewyp_pdf", lambda _form: b"pdf-bytes")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/sessions/{stub_current_session.id}/forms/1/pdf",
            headers={"Authorization": "Bearer abc"},
        )
    assert resp.status_code == 200
    assert resp.content == b"pdf-bytes"
    assert resp.headers["content-type"] == "application/pdf"


