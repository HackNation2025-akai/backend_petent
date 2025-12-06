from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    case_ref: str | None = None
    form_type: str = "EWYP"
    metadata: dict | None = None


class SessionResponse(BaseModel):
    session_id: uuid.UUID
    session_token: str | None = None
    expires_at: datetime
    status: str
    form_type: str


class FormSubmitRequest(BaseModel):
    payload: dict
    source: Literal["raw", "corrected"] = "raw"
    comment: str | None = None


class FormSubmitResponse(BaseModel):
    version: int
    created_at: datetime


class FormValidateRequest(BaseModel):
    payload: dict
    fields_to_validate: list[str] | None = None


class FieldValidationResult(BaseModel):
    field_path: str
    status: Literal["success", "objection"]
    justification: str


class FormValidateResponse(BaseModel):
    version: int
    results: list[FieldValidationResult]
    summary: dict


class VersionSummary(BaseModel):
    version: int
    source: str
    created_at: datetime
    comment: str | None


class HistoryResponse(BaseModel):
    session_id: uuid.UUID
    total_versions: int
    versions: list[VersionSummary]


class FormSnapshotResponse(BaseModel):
    version: int
    source: str
    payload: dict
    validations: list[FieldValidationResult]
    created_at: datetime


