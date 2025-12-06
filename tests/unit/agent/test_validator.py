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


