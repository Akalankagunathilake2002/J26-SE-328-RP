import contextlib
from fastapi import APIRouter, FastAPI

from app.api.routers import health_router
from app.config.settings import get_settings


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    from app.db.session import dispose_engine

    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.service_name,
        version=settings.version,
        lifespan=lifespan,
        docs_url="/api/v1/profile/docs",
        redoc_url=None,
        openapi_url="/api/v1/profile/openapi.json",
    )

    profile_router = APIRouter(prefix="/api/v1/profile")
    profile_router.include_router(health_router)

    app.include_router(profile_router)
    app.include_router(health_router)

    return app


app = create_app()
