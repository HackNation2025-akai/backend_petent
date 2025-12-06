from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_session, get_session
from app.models.session import SessionCreateRequest, SessionResponse
from app.services.session_service import close_session, create_session, refresh_token

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_endpoint(
    payload: SessionCreateRequest,
    db: AsyncSession = Depends(get_session),  # noqa: B008 FastAPI dependency
) -> SessionResponse:
    session, token = await create_session(db, payload.form_type, payload.case_ref)
    return SessionResponse(
        session_id=session.id,
        session_token=token,
        expires_at=session.token_expires_at,
        status=session.status,
        form_type=session.form_type,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_status(
    session=Depends(get_current_session),  # noqa: B008
) -> SessionResponse:
    return SessionResponse(
        session_id=session.id,
        session_token=None,
        expires_at=session.token_expires_at,
        status=session.status,
        form_type=session.form_type,
    )


@router.post("/sessions/{session_id}/refresh-token", response_model=SessionResponse)
async def refresh_session_token(
    session_id: uuid.UUID,
    _session=Depends(get_current_session),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> SessionResponse:
    session, token = await refresh_token(db, session_id)
    return SessionResponse(
        session_id=session.id,
        session_token=token,
        expires_at=session.token_expires_at,
        status=session.status,
        form_type=session.form_type,
    )


@router.post("/sessions/{session_id}/close")
async def close_session_endpoint(
    session_id: uuid.UUID,
    _session=Depends(get_current_session),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict:
    try:
        session = await close_session(db, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"session_id": str(session.id), "status": session.status}


