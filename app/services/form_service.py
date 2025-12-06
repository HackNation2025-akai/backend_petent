from __future__ import annotations

import hashlib
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.config_loader import config_loader
from app.agent.validator import run_validation_agent
from app.db.models import FieldValidation, FormSession, FormVersion


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _get_by_path(payload: dict, dotted_path: str) -> Any:
    current: Any = payload
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


async def _ensure_open_session(db: AsyncSession, session_id: uuid.UUID) -> FormSession:
    result = await db.execute(select(FormSession).where(FormSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise ValueError("Session not found")
    if session.status == "closed":
        raise ValueError("Session is closed")
    return session


async def _next_version(db: AsyncSession, session_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.max(FormVersion.version)).where(FormVersion.session_id == session_id)
    )
    current_max = result.scalar_one_or_none() or 0
    return current_max + 1


async def submit_form(
    db: AsyncSession,
    session_id: uuid.UUID,
    payload: dict,
    source: str = "raw",
    comment: str | None = None,
) -> FormVersion:
    await _ensure_open_session(db, session_id)
    version_number = await _next_version(db, session_id)
    version = FormVersion(
        session_id=session_id,
        version=version_number,
        payload=payload,
        source=source,
        comment=comment,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version


async def validate_form(
    db: AsyncSession,
    session_id: uuid.UUID,
    payload: dict,
    fields_to_validate: list[str] | None = None,
) -> tuple[FormVersion, list[FieldValidation]]:
    await _ensure_open_session(db, session_id)
    version_number = await _next_version(db, session_id)
    version = FormVersion(
        session_id=session_id,
        version=version_number,
        payload=payload,
        source="raw",
        comment="validation",
    )
    db.add(version)
    await db.flush()

    mapping = config_loader.field_mapping or {}
    selected_fields = (
        [f for f in fields_to_validate if f in mapping] if fields_to_validate else list(mapping.keys())
    )

    validations: list[FieldValidation] = []
    for field_path in selected_fields:
        field_type = mapping.get(field_path)
        if not field_type:
            continue
        value = _get_by_path(payload, field_path)
        if value is None:
            continue
        # Ensure string for agent
        value_str = str(value)
        agent_result = await run_validation_agent(field_type, value_str, None)
        validation = FieldValidation(
            version_id=version.id,
            field_path=field_path,
            field_type=field_type,
            value_hash=_hash_value(value_str),
            status=agent_result.status,
            justification=agent_result.justification,
        )
        db.add(validation)
        validations.append(validation)

    await db.commit()
    await db.refresh(version)
    for validation in validations:
        await db.refresh(validation)
    return version, validations


async def get_history(
    db: AsyncSession, session_id: uuid.UUID, limit: int = 10, offset: int = 0
) -> tuple[int, list[FormVersion]]:
    total_query = await db.execute(
        select(func.count(FormVersion.id)).where(FormVersion.session_id == session_id)
    )
    total = int(total_query.scalar_one_or_none() or 0)

    result = await db.execute(
        select(FormVersion)
        .where(FormVersion.session_id == session_id)
        .order_by(FormVersion.version.desc())
        .offset(offset)
        .limit(limit)
    )
    versions = list(result.scalars().all())
    return total, versions


async def get_version(db: AsyncSession, session_id: uuid.UUID, version: int) -> FormVersion | None:
    result = await db.execute(
        select(FormVersion)
        .where(FormVersion.session_id == session_id, FormVersion.version == version)
        .options(selectinload(FormVersion.validations))
    )
    return result.scalar_one_or_none()


