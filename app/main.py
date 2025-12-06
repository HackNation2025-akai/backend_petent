import asyncio
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.logging import logger
from app.db.models import Base
from app.db.session import engine


async def _wait_for_db(connect_fn: Callable[[], Awaitable[object]], attempts: int = 10, delay: float = 1.0) -> None:
    """Retry DB connectivity before running migrations."""
    last_exc: Exception | None = None
    for idx in range(1, attempts + 1):
        try:
            await connect_fn()
            return
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.info("DB not ready, retry %s/%s (%s)", idx, attempts, exc)
            await asyncio.sleep(delay)
    raise RuntimeError(f"Database not ready after {attempts} attempts") from last_exc


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def connect_and_create() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    await _wait_for_db(connect_and_create)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router, prefix="/api")


