from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthServiceDep, CurrentUserDep, SettingsDep
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import EmailAlreadyRegisteredError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(request: RegisterRequest, service: AuthServiceDep) -> User:
    try:
        return await service.register(request.full_name, request.email, request.password)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "An account with this email already exists"
        ) from None


@router.post("/login")
async def login(request: LoginRequest, service: AuthServiceDep, settings: SettingsDep) -> TokenResponse:
    user = await service.authenticate(request.email, request.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return TokenResponse(
        access_token=service.issue_token(user),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUserDep) -> User:
    return user
