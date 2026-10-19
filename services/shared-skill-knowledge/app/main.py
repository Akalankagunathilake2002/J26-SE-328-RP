import contextlib
from fastapi import FastAPI, APIRouter
from app.api.routers import (
    domains_router,
    skills_router,
    roles_router,
    normalization_router,
    candidates_router,
    relationships_router,
    candidate_relationships_router,
    skill_domains_router,
    role_domains_router,
    snapshots_router,
)
from fastapi.middleware.cors import CORSMiddleware
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

    # Enable CORS for local development and gateway routing.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ssks_router = APIRouter(prefix="/ssks")

    @ssks_router.get("/health", tags=["health"])
    async def health_check():
        return {"status": "healthy", "service": "shared-skill-knowledge"}

    ssks_router.include_router(domains_router)
    ssks_router.include_router(skills_router)
    ssks_router.include_router(roles_router)
    ssks_router.include_router(normalization_router)
    ssks_router.include_router(candidates_router)
    ssks_router.include_router(relationships_router)
    ssks_router.include_router(candidate_relationships_router)
    ssks_router.include_router(skill_domains_router)
    ssks_router.include_router(role_domains_router)
    ssks_router.include_router(snapshots_router)

    app.include_router(ssks_router)

    return app

app = create_app()
