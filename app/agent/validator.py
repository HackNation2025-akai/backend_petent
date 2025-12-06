from __future__ import annotations
# ruff: noqa: I001

import json
from typing import Literal

from app.agent.config_loader import config_loader
from app.core.llm import get_llm
from app.core.logging import logger
from pydantic import BaseModel, ValidationError

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

    logger.info("Validation start field=%s len=%d", field_type, len(value))

    llm = get_llm()
    messages = config_loader.build_messages(field_type, value, context)
    if not messages:
        return AgentResult(status="objection", justification="Unsupported field type.")

    logger.debug("LLM payload: %s", messages[-1].content)
    response = await llm.ainvoke(messages)
    raw_content = response.content
    if not isinstance(raw_content, str):
        try:
            raw_content = json.dumps(raw_content)
        except Exception:  # noqa: BLE001
            raw_content = str(raw_content)
    logger.debug("LLM raw response: %s", raw_content[:500])

    try:
        parsed = json.loads(raw_content)
        if not isinstance(parsed, dict):
            raise TypeError("LLM response is not an object")
        logger.debug("LLM parsed response dict: %s", parsed)
        result = AgentResult(**parsed)
    except (json.JSONDecodeError, ValidationError, TypeError):
        fallback_message = (raw_content or "Brak odpowiedzi modelu. Zwracam objection.").strip()
        if len(fallback_message) > 200:
            fallback_message = fallback_message[:197] + "..."
        logger.debug("LLM parse fallback used. raw_content=%s fallback=%s", raw_content, fallback_message)
        result = AgentResult(status="objection", justification=fallback_message)

    # Enforce non-empty justification
    if not result.justification.strip():
        result = AgentResult(status="objection", justification="Brak odpowiedzi modelu. Zwracam objection.")

    # Enforce valid3 allowed classifications (only dentist/hairdresser)
    if field_type == "valid3" and result.status == "success":
        msg_lower = result.justification.lower()
        allowed = [t.lower() for t in field_cfg.allowed_terms]
        if allowed and not any(token in msg_lower for token in allowed):
            result = AgentResult(
                status="objection",
                justification="Not a supported profession (only dentist or hairdresser).",
            )

    logger.info("Validation result field=%s status=%s", field_type, result.status)
    logger.debug("Validation justification field=%s justification=%s", field_type, result.justification)

    return result


