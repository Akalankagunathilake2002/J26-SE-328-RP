from app.api.routers.domains import router as domains_router
from app.api.routers.skills import router as skills_router
from app.api.routers.roles import router as roles_router
from app.api.routers.normalization import router as normalization_router
from app.api.routers.candidates import router as candidates_router
from app.api.routers.relationships import router as relationships_router
from app.api.routers.candidate_relationships import router as candidate_relationships_router
from app.api.routers.skill_domains import router as skill_domains_router
from app.api.routers.role_domains import router as role_domains_router

__all__ = [
    "domains_router",
    "skills_router",
    "roles_router",
    "normalization_router",
    "candidates_router",
    "relationships_router",
    "candidate_relationships_router",
    "skill_domains_router",
    "role_domains_router",
]
