import uuid

from sqlalchemy.exc import IntegrityError

from app.config.settings import Settings
from app.core.security import create_access_token, hash_password, read_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class EmailAlreadyRegisteredError(Exception):
    pass


class AuthService:
    """Registers users, checks credentials and issues access tokens."""

    def __init__(self, repository: UserRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    async def register(self, full_name: str, email: str, password: str) -> User:
        email = email.lower()
        if await self.repository.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError(email)
        user = User(full_name=full_name, email=email, password_hash=hash_password(password))
        try:
            return await self.repository.add(user)
        except IntegrityError as exc:  # registered concurrently
            raise EmailAlreadyRegisteredError(email) from exc

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.repository.get_by_email(email.lower())
        if not verify_password(password, user.password_hash if user else None):
            return None
        return user

    def issue_token(self, user: User) -> str:
        return create_access_token(user.id, self.settings)

    async def user_from_token(self, token: str) -> User | None:
        user_id: uuid.UUID | None = read_access_token(token, self.settings)
        return await self.repository.get_by_id(user_id) if user_id else None
