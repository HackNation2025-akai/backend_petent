from typing import Literal

from pydantic import BaseModel, Field


class ValidationRequest(BaseModel):
    field_type: str = Field(..., description="Typ pola dostarczony przez frontend, np. text/email/phone/number/select")
    value: str = Field(..., description="Wartość pola do oceny")
    context: str | None = Field(default=None, description="Opcjonalny kontekst biznesowy")


class ValidationResponse(BaseModel):
    status: Literal["success", "objection"]
    message: str


