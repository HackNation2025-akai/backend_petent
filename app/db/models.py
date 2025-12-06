from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ValidationLog(Base):
    __tablename__ = "validation_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FormSession(Base):
    __tablename__ = "form_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    form_type: Mapped[str] = mapped_column(String(50), default="EWYP")
    case_ref: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")
    session_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    versions: Mapped[list["FormVersion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class FormVersion(Base):
    __tablename__ = "form_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("form_sessions.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["FormSession"] = relationship(back_populates="versions")
    validations: Mapped[list["FieldValidation"]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("session_id", "version"),)


class FieldValidation(Base):
    __tablename__ = "field_validations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("form_versions.id"), nullable=False)
    field_path: Mapped[str] = mapped_column(String(100), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    version: Mapped["FormVersion"] = relationship(back_populates="validations")


