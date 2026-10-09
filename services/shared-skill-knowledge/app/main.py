import contextlib
from fastapi import FastAPI, APIRouter
from app.api.routers import domains_router, skills_router, roles_router
from app.config.settings import get_settings

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import dispose_engine, create_tables
    await create_tables()
    yield
    await dispose_engine()

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.service_name,
        version=settings.version,
        lifespan=lifespan,
        docs_url="/ssks/docs",
        redoc_url=None,
        openapi_url="/ssks/openapi.json"
    )

    ssks_router = APIRouter(prefix="/ssks")

    @ssks_router.get("/health", tags=["health"])
    async def health_check():
        return {"status": "healthy", "service": "shared-skill-knowledge"}

    ssks_router.include_router(domains_router)
    ssks_router.include_router(skills_router)
    ssks_router.include_router(roles_router)

    app.include_router(ssks_router)

    return app

app = create_app()
