from __future__ import annotations
# ruff: noqa: I001

import json
from typing import Literal

from pydantic import BaseModel, ValidationError

from app.agent.config_loader import config_loader
from app.core.llm import get_llm

class AgentResult(BaseModel):
    status: Literal["success", "objection"]
    justification: str


async def run_validation_agent(field_type: str, value: str, context: str | None = None) -> AgentResult:
    """Uruchamia agenta LangChain i zwraca wynik walidacji."""
    field_cfg = config_loader.get_field(field_type)
    if not field_cfg:
        return AgentResult(status="objection", justification="Unsupported field type.")
    if not value.strip():
        return AgentResult(status="objection", justification="Value is empty. Please provide a value.")

    llm = get_llm()
    messages = config_loader.build_messages(field_type, value, context)
    if not messages:
        return AgentResult(status="objection", justification="Unsupported field type.")

    response = await llm.ainvoke(messages)
    raw_content = response.content
    if not isinstance(raw_content, str):
        try:
            raw_content = json.dumps(raw_content)
        except Exception:  # noqa: BLE001
            raw_content = str(raw_content)

    try:
        parsed = json.loads(raw_content)
        if not isinstance(parsed, dict):
            raise TypeError("LLM response is not an object")
        result = AgentResult(**parsed)
    except (json.JSONDecodeError, ValidationError, TypeError):
        fallback_message = (raw_content or "No response from model.").strip()
        if len(fallback_message) > 200:
            fallback_message = fallback_message[:197] + "..."
        result = AgentResult(status="objection", justification=fallback_message)

    # Enforce non-empty justification
    if not result.justification.strip():
        result = AgentResult(status="objection", justification="Empty response from model.")

    # Enforce valid3 allowed classifications (only dentist/hairdresser)
    if field_type == "valid3" and result.status == "success":
        msg_lower = result.justification.lower()
        allowed = [t.lower() for t in field_cfg.allowed_terms]
        if allowed and not any(token in msg_lower for token in allowed):
            result = AgentResult(
                status="objection",
                justification="Not a supported profession (only dentist or hairdresser).",
            )

    return result


