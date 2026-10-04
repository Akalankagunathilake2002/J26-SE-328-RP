from fastapi import APIRouter

from app.api.dependencies import SettingsDep

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: SettingsDep) -> dict[str, str]:
    return {"status": "healthy", "service": settings.service_name}
