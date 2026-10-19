from app.api.routers.analyses import router as analyses_router
from app.api.routers.health import router as health_router
from app.api.routers.industry_profiles import router as industry_profiles_router

__all__ = ["analyses_router", "health_router", "industry_profiles_router"]
