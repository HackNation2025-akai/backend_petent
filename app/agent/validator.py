from __future__ import annotations
# ruff: noqa: I001

import json
import re
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
        # Stały komunikat dla pustej wartości, bez angażowania LLM
        return AgentResult(status="objection", justification="To pole nie może być puste.")

    logger.info("Validation start field=%s len=%d", field_type, len(value))

    # Prosta, deterministyczna walidacja dla wybranych pól opartych na regexach
    # aby nie obciążać LLM i mieć przewidywalne komunikaty.
    if field_type == "pesel_strict":
        if len(value) != 11 or not value.isdigit():
            return AgentResult(status="objection", justification="Numer PESEL ma dokładnie 11 cyfr.")
        return AgentResult(status="success", justification="")

    if field_type == "name_proper":
        if not value[0].isupper() or not value.replace("-", "").isalpha():
            return AgentResult(
                status="objection",
                justification="Imię i nazwisko powinno zawierać tylko litery i zaczynać się wielką literą.",
            )
        return AgentResult(status="success", justification="")

    if field_type == "city_proper":
        # Tu polegamy na walidacji regex po stronie backendu,
        # ale zwracamy stały komunikat w razie błędu.
        return AgentResult(status="success", justification="")

    if field_type == "doc_number":
        if not (5 <= len(value) <= 12) or not value.isalnum():
            return AgentResult(
                status="objection",
                justification="Seria i numer dokumentu powinny zawierać 5-12 znaków alfanumerycznych",
            )
        return AgentResult(status="success", justification="")

    if field_type == "phone_digits":
        digits_only = "".join(ch for ch in value if ch.isdigit())
        if not (7 <= len(digits_only) <= 15):
            return AgentResult(
                status="objection",
                justification="Numer telefonu powinien zawierać 9 cyfr (spacje i kreski są dozwolone)",
            )
        return AgentResult(status="success", justification="")

    if field_type == "street_text":
        clean = value.strip()
        if len(clean) < 3:
            return AgentResult(
                status="objection",
                justification="Nazwa ulicy powinna mieć co najmniej 3 znaki.",
            )
        # Pozwól na litery/cyfry/spacje/myślniki/kropki
        if not all(ch.isalnum() or ch in {" ", "-", ".", "/"} for ch in clean):
            return AgentResult(
                status="objection",
                justification="Nazwa ulicy może zawierać litery, cyfry, spacje i myślniki.",
            )
        return AgentResult(status="success", justification="")

    if field_type == "house_number":
        clean = value.strip()
        # 1–4 cyfry + opcjonalna litera na końcu (np. 10A)
        if not clean or not clean[0].isdigit():
            return AgentResult(
                status="objection",
                justification="Numer domu powinien zaczynać się od cyfry.",
            )
        digits = "".join(ch for ch in clean if ch.isdigit())
        if not (1 <= len(digits) <= 4):
            return AgentResult(
                status="objection",
                justification="Numer domu powinien składać się z 1–4 cyfr.",
            )
        if len(clean) > len(digits):
            suffix = clean[len(digits) :]
            if not suffix.isalpha() or len(suffix) > 2:
                return AgentResult(
                    status="objection",
                    justification="Po cyfrach numeru domu może wystąpić krótki sufiks literowy (np. A).",
                )
        return AgentResult(status="success", justification="")

    if field_type == "postal_code_pl":
        clean = value.strip()
        if len(clean) != 6 or clean[2] != "-" or not (clean[:2] + clean[3:]).isdigit():
            return AgentResult(
                status="objection",
                justification="Kod pocztowy powinien mieć format 00-000.",
            )
        return AgentResult(status="success", justification="")

    pattern = getattr(field_cfg, "pattern", None)
    if pattern:
        if not re.fullmatch(pattern, value):
            return AgentResult(
                status="objection",
                justification=field_cfg.description or "Wartość ma nieprawidłowy format.",
            )

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

    # Enforce niepusty komunikat tylko dla objection; przy success
    # frontend może bezpiecznie założyć brak komunikatu.
    if result.status == "objection" and not result.justification.strip():
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


