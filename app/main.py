from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import settings
from app.db.models import Base
from app.db.session import engine

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.on_event("startup")
async def on_startup() -> None:
    # Auto-create tables to survive clean DB volumes
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router, prefix="/api")


