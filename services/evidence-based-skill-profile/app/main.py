import contextlib
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    extraction_router, health_router, normalisation_router, profile_router,
)
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
    # The website calls the service from the browser. Through Docker the gateway sets CORS headers
    # (and drops these); this lets the website call the service directly during local development.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_router = APIRouter(prefix="/api/v1/profile")
    api_router.include_router(health_router)
    api_router.include_router(extraction_router)
    api_router.include_router(normalisation_router)
    api_router.include_router(profile_router)

    app.include_router(api_router)
    app.include_router(health_router)
    app.openapi = lambda: _openapi_with_file_pickers(app)

    return app


def _openapi_with_file_pickers(app: FastAPI) -> dict:
    """OpenAPI schema where upload fields also carry `format: binary`.

    FastAPI marks uploads with OpenAPI 3.1's `contentMediaType`, but Swagger UI only shows a
    "Choose file" button for `format: binary`, so lists of files appeared as text boxes.
    """
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)

    def mark(node):
        if isinstance(node, dict):
            if node.get("contentMediaType") == "application/octet-stream":
                node["format"] = "binary"
            for value in node.values():
                mark(value)
        elif isinstance(node, list):
            for value in node:
                mark(value)

    mark(schema)
    app.openapi_schema = schema
    return schema


app = create_app()
