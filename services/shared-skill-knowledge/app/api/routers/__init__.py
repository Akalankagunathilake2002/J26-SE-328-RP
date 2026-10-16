from app.api.routers.domains import router as domains_router
from app.api.routers.skills import router as skills_router
from app.api.routers.roles import router as roles_router
from app.api.routers.normalization import router as normalization_router
from app.api.routers.candidates import router as candidates_router

__all__ = [
    "domains_router",
    "skills_router",
    "roles_router",
    "normalization_router",
    "candidates_router",
]
