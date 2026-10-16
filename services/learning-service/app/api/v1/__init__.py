from fastapi import APIRouter
from app.api.v1.learning_router import router as learning_router
from app.api.v1.progress_router import router as progress_router
from app.api.v1.research_router import router as research_router
from app.api.v1.upstream_router import router as upstream_router
from app.api.v1.analytics_router import router as analytics_router

api_v1_router = APIRouter()
api_v1_router.include_router(learning_router)
api_v1_router.include_router(progress_router)
api_v1_router.include_router(research_router)
api_v1_router.include_router(upstream_router)
api_v1_router.include_router(analytics_router)

__all__ = ["api_v1_router"]
