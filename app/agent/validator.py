from __future__ import annotations

import json
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from app.core.llm import get_llm

SUPPORTED_FIELD_TYPES = {
    "text",
    "email",
    "phone",
    "number",
    "select",
    "valid1",  # 11-digit numeric (PESEL-like)
    "valid2",  # Letters (A-Z + PL diacritics), start with capital
    "valid3",  # Profession classification: dentist, hairdresser, other
}

FIELD_RULES: dict[str, str] = {
    "valid1": (
        "Treat as PESEL-like: must be exactly 11 digits (0-9 only). "
        "Return objection if not 11 digits or contains non-digits."
    ),
    "valid2": (
        "Must contain only letters A-Z (case-insensitive) including Polish diacritics "
        "(ą, ć, ę, ł, ń, ó, ś, ż, ź). Must start with an uppercase letter. "
        "If any other characters or first letter not uppercase -> objection."
    ),
    "valid3": (
        "Classify the text into one of: dentist, hairdresser, other. "
        "If clearly dentist or hairdresser -> success. Otherwise -> objection with a brief hint."
    ),
}


SYSTEM_PROMPT = (
    "You are a concise form-field reviewer. Decide if a provided value fits its field type "
    "using the supplied rules. Always return JSON with keys 'status' and 'message'. "
    "status: 'success' or 'objection'. message: short suggestion (<=200 chars). "
    "If the value is unclear or ill-formatted for its type, return 'objection' with a hint."
)


class AgentResult(BaseModel):
    status: Literal["success", "objection"]
    message: str


async def run_validation_agent(field_type: str, value: str, context: str | None = None) -> AgentResult:
    """Uruchamia agenta LangChain i zwraca wynik walidacji."""
    if field_type not in SUPPORTED_FIELD_TYPES:
        return AgentResult(status="objection", message="Unsupported field type.")
    if not value.strip():
        return AgentResult(status="objection", message="Value is empty. Please provide a value.")

    llm = get_llm()
    payload = {
        "field_type": field_type,
        "value": value,
        "context": context or "",
        "rules": FIELD_RULES.get(field_type, ""),
        "allowed_status": ["success", "objection"],
    }
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=json.dumps(payload)),
    ]

    response = await llm.ainvoke(messages)
    raw_content = response.content

    try:
        parsed = json.loads(raw_content)
        result = AgentResult(**parsed)
    except (json.JSONDecodeError, ValidationError):
        fallback_message = (raw_content or "No response from model.").strip()
        if len(fallback_message) > 200:
            fallback_message = fallback_message[:197] + "..."
        result = AgentResult(status="objection", message=fallback_message)

    return result


