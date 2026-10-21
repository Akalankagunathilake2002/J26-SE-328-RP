from app.api.routers.extraction import router as extraction_router
from app.api.routers.health import router as health_router
from app.api.routers.normalisation import router as normalisation_router

__all__ = ["extraction_router", "health_router", "normalisation_router"]
