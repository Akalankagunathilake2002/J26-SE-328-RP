import contextlib

from fastapi import APIRouter, FastAPI

from app.api.routers import analyses_router, health_router, industry_profiles_router
from app.config.settings import get_settings


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import create_tables, dispose_engine

    # Ensure database schema is initialized on startup, matching shared-skill-knowledge
    await create_tables()
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.service_name,
        version=settings.version,
        lifespan=lifespan,
        docs_url="/readiness/docs",
        redoc_url=None,
        openapi_url="/readiness/openapi.json",
    )

    readiness_router = APIRouter(prefix="/readiness")
    readiness_router.include_router(health_router)
    readiness_router.include_router(analyses_router)
    readiness_router.include_router(industry_profiles_router)

    app.include_router(readiness_router)
    app.include_router(health_router)
    app.include_router(analyses_router)
    app.include_router(industry_profiles_router)

    return app


app = create_app()
