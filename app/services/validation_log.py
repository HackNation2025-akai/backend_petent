from __future__ import annotations

import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.validator import AgentResult
from app.db.models import ValidationLog


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


async def log_validation(
    session: AsyncSession,
    field_type: str,
    value: str,
    result: AgentResult,
) -> None:
    record = ValidationLog(
        field_type=field_type,
        value_hash=_hash_value(value),
        status=result.status,
        message=result.justification,
    )
    session.add(record)
    await session.commit()


