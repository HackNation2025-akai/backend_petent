from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_session_token, get_token_expiry
from app.db.models import FormSession


async def _get_session(db: AsyncSession, session_id: uuid.UUID) -> FormSession | None:
    result = await db.execute(select(FormSession).where(FormSession.id == session_id))
    return result.scalar_one_or_none()


async def create_session(
    db: AsyncSession, form_type: str = "EWYP", case_ref: str | None = None
) -> tuple[FormSession, str]:
    token, token_hash = generate_session_token()
    session = FormSession(
        form_type=form_type,
        case_ref=case_ref,
        status="open",
        session_token_hash=token_hash,
        token_expires_at=get_token_expiry(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session, token


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> FormSession | None:
    return await _get_session(db, session_id)


async def refresh_token(db: AsyncSession, session_id: uuid.UUID) -> tuple[FormSession, str]:
    session = await _get_session(db, session_id)
    if not session:
        raise ValueError("Session not found")
    if session.status == "closed":
        raise ValueError("Session is closed")

    token, token_hash = generate_session_token()
    session.session_token_hash = token_hash
    session.token_expires_at = get_token_expiry()
    await db.commit()
    await db.refresh(session)
    return session, token


async def close_session(db: AsyncSession, session_id: uuid.UUID) -> FormSession:
    session = await _get_session(db, session_id)
    if not session:
        raise ValueError("Session not found")

    session.status = "closed"
    session.closed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session


