from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FormSession
from app.db.session import get_session


def generate_session_token() -> tuple[str, str]:
    """Zwraca (raw_token, hash_for_db)."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


def verify_session_token(raw_token: str, stored_hash: str) -> bool:
    return hashlib.sha256(raw_token.encode()).hexdigest() == stored_hash


def get_token_expiry(hours: int = 2) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


async def get_current_session(
    session_id: uuid.UUID,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> FormSession:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")

    raw_token = authorization.split(" ", maxsplit=1)[1].strip()
    result = await db.execute(select(FormSession).where(FormSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if session.status == "closed":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session is closed")

    if session.token_expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    if not verify_session_token(raw_token, session.session_token_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return session


