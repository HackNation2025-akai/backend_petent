from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_session, get_session
from app.models.ewyp import EWYPFormSchema
from app.models.session import (
    FieldValidationResult,
    FormSnapshotResponse,
    FormSubmitRequest,
    FormSubmitResponse,
    FormValidateRequest,
    FormValidateResponse,
    HistoryResponse,
    VersionSummary,
)
from app.services.form_service import (
    get_history,
    get_version,
    submit_form,
    validate_form,
)
from app.services.pdf_export import generate_ewyp_pdf, generate_notification_pdf

router = APIRouter()


@router.post(
    "/sessions/{session_id}/forms",
    response_model=FormSubmitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_form_endpoint(
    session_id: uuid.UUID,
    payload: FormSubmitRequest,
    _session=Depends(get_current_session),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> FormSubmitResponse:
    try:
        version = await submit_form(db, session_id, payload.payload, payload.source, payload.comment)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FormSubmitResponse(version=version.version, created_at=version.created_at)


@router.post("/sessions/{session_id}/validate", response_model=FormValidateResponse)
async def validate_form_endpoint(
    session_id: uuid.UUID,
    payload: FormValidateRequest,
    _session=Depends(get_current_session),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> FormValidateResponse:
    try:
        version, validations = await validate_form(
            db, session_id, payload.payload, payload.fields_to_validate
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    summary = {"success": 0, "objection": 0}
    results: list[FieldValidationResult] = []
    for item in validations:
        summary[item.status] = summary.get(item.status, 0) + 1
        results.append(
            FieldValidationResult(
                field_path=item.field_path,
                status=item.status,  # type: ignore[arg-type]
                justification=item.justification,
            )
        )
    return FormValidateResponse(version=version.version, results=results, summary=summary)


@router.get("/sessions/{session_id}/history", response_model=HistoryResponse)
async def get_history_endpoint(
    session_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _session=Depends(get_current_session),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> HistoryResponse:
    total, versions = await get_history(db, session_id, limit, offset)
    return HistoryResponse(
        session_id=session_id,
        total_versions=total,
        versions=[
            VersionSummary(
                version=v.version,
                source=v.source,
                created_at=v.created_at,
                comment=v.comment,
            )
            for v in versions
        ],
    )


@router.get("/sessions/{session_id}/forms/{version}", response_model=FormSnapshotResponse)
async def get_form_version(
    session_id: uuid.UUID,
    version: int,
    _session=Depends(get_current_session),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> FormSnapshotResponse:
    record = await get_version(db, session_id, version)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return FormSnapshotResponse(
        version=record.version,
        source=record.source,
        payload=record.payload,
        validations=[
            FieldValidationResult(
                field_path=v.field_path,
                status=v.status,  # type: ignore[arg-type]
                justification=v.justification,
            )
            for v in record.validations
        ],
        created_at=record.created_at,
    )


@router.get("/sessions/{session_id}/forms/{version}/pdf")
async def get_form_pdf(
    session_id: uuid.UUID,
    version: int,
    db: AsyncSession = Depends(get_session),
) -> Response:
    record = await get_version(db, session_id, version)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    try:
        pdf_bytes = generate_ewyp_pdf(EWYPFormSchema(**record.payload))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.get("/sessions/{session_id}/forms/{version}/pdf-notification")
async def get_form_notification_pdf(
    session_id: uuid.UUID,
    version: int,
    db: AsyncSession = Depends(get_session),
) -> Response:
    record = await get_version(db, session_id, version)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    try:
        pdf_bytes = generate_notification_pdf(EWYPFormSchema(**record.payload))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    return Response(content=pdf_bytes, media_type="application/pdf")


