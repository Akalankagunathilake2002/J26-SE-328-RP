from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth, health
from app.config.settings import get_settings
from app.db.session import create_tables, dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await create_tables()
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    # Docs live under /auth so they are reachable through the API gateway's /auth/ route.
    app = FastAPI(
        title=settings.service_name,
        version=settings.version,
        lifespan=lifespan,
        docs_url="/auth/docs",
        redoc_url=None,
        openapi_url="/auth/openapi.json",
    )

    app.include_router(health.router)
    app.include_router(auth.router)

    return app


app = create_app()
