import json

import pytest

from app.agent.validator import AgentResult, run_validation_agent


class _FakeLLMResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeLLM:
    def __init__(self, content: str):
        self._content = content

    async def ainvoke(self, _messages):
        return _FakeLLMResponse(self._content)


@pytest.mark.asyncio
async def test_agent_success(monkeypatch):
    fake_llm = _FakeLLM(json.dumps({"status": "success", "message": "ok"}))
    monkeypatch.setattr("app.agent.validator.get_llm", lambda: fake_llm)

    result = await run_validation_agent("text", "Acme", None)
    assert result == AgentResult(status="success", message="ok")


@pytest.mark.asyncio
async def test_agent_empty_value(monkeypatch):
    fake_llm = _FakeLLM(json.dumps({"status": "success", "message": "ok"}))
    monkeypatch.setattr("app.agent.validator.get_llm", lambda: fake_llm)

    result = await run_validation_agent("text", "   ", None)
    assert result.status == "objection"
    assert "empty" in result.message.lower()


@pytest.mark.asyncio
async def test_agent_unsupported_type(monkeypatch):
    fake_llm = _FakeLLM(json.dumps({"status": "success", "message": "ok"}))
    monkeypatch.setattr("app.agent.validator.get_llm", lambda: fake_llm)

    result = await run_validation_agent("unknown", "value", None)
    assert result.status == "objection"
    assert "unsupported" in result.message.lower()


@pytest.mark.asyncio
async def test_agent_malformed_response(monkeypatch):
    fake_llm = _FakeLLM("not-json")
    monkeypatch.setattr("app.agent.validator.get_llm", lambda: fake_llm)

    result = await run_validation_agent("text", "Acme", None)
    assert result.status == "objection"
    assert result.message


@pytest.mark.asyncio
async def test_agent_nonstring_response(monkeypatch):
    fake_llm = _FakeLLM([{"status": "success", "message": "ok"}])
    monkeypatch.setattr("app.agent.validator.get_llm", lambda: fake_llm)

    result = await run_validation_agent("text", "Acme", None)
    # Should not crash; will likely fail to parse JSON list -> objection with stringified content
    assert result.status == "objection"


@pytest.mark.asyncio
async def test_agent_valid1_success(monkeypatch):
    fake_llm = _FakeLLM(json.dumps({"status": "success", "message": "ok"}))
    monkeypatch.setattr("app.agent.validator.get_llm", lambda: fake_llm)

    result = await run_validation_agent("valid1", "12345678901", None)
    assert result.status == "success"


@pytest.mark.asyncio
async def test_agent_valid1_fail(monkeypatch):
    fake_llm = _FakeLLM(json.dumps({"status": "objection", "message": "needs 11 digits"}))
    monkeypatch.setattr("app.agent.validator.get_llm", lambda: fake_llm)

    result = await run_validation_agent("valid1", "abc", None)
    assert result.status == "objection"
    assert "11" in result.message or "digit" in result.message.lower()


@pytest.mark.asyncio
async def test_agent_valid2_success(monkeypatch):
    fake_llm = _FakeLLM(json.dumps({"status": "success", "message": "ok"}))
    monkeypatch.setattr("app.agent.validator.get_llm", lambda: fake_llm)

    result = await run_validation_agent("valid2", "Łódź", None)
    assert result.status == "success"


@pytest.mark.asyncio
async def test_agent_valid2_fail(monkeypatch):
    fake_llm = _FakeLLM(json.dumps({"status": "objection", "message": "letters only"}))
    monkeypatch.setattr("app.agent.validator.get_llm", lambda: fake_llm)

    result = await run_validation_agent("valid2", "12City", None)
    assert result.status == "objection"


@pytest.mark.asyncio
async def test_agent_valid3_classification(monkeypatch):
    fake_llm = _FakeLLM(json.dumps({"status": "success", "message": "dentist"}))
    monkeypatch.setattr("app.agent.validator.get_llm", lambda: fake_llm)

    result = await run_validation_agent("valid3", "Gabinet stomatologiczny", None)
    assert result.status == "success"


