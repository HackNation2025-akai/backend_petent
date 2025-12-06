from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.validator import run_validation_agent
from app.db.session import get_session
from app.models.schemas import ValidationRequest, ValidationResponse
from app.services.validation_log import log_validation

router = APIRouter()


@router.post("/validate", response_model=ValidationResponse)
async def validate_field(
    payload: ValidationRequest,
    session: AsyncSession = Depends(get_session),  # noqa: B008 FastAPI dependency injection
) -> ValidationResponse:
    result = await run_validation_agent(payload.field_type, payload.value, payload.context)
    await log_validation(session, payload.field_type, payload.value, result)
    return ValidationResponse(status=result.status, justification=result.justification)


