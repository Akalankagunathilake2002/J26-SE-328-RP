from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import time
import uuid

import httpx
import jwt
from fastapi import HTTPException, status

from app.config.settings import Settings

ROLE_ADMIN = "ADMIN"
ROLE_HR = "HR"
ROLE_USER = "USER"
ROLE_SERVICE = "SERVICE"
SUPPORTED_ROLES = frozenset({ROLE_ADMIN, ROLE_HR, ROLE_USER, ROLE_SERVICE})

_ROLE_CACHE_TTL_SECONDS = 30.0
_MAX_CACHE_SIZE = 1024
_role_cache: dict[str, tuple[float, uuid.UUID, str]] = {}


@dataclass(frozen=True)
class Principal:
    """Authenticated caller identity derived from a verified JWT and Auth profile."""

    user_id: uuid.UUID
    role: str
    issuer: str | None
    audience: str | list[str] | None
    issued_at: datetime
    expires_at: datetime


class TokenValidationError(Exception):
    """Raised when a bearer token fails cryptographic or claim validation."""


def clear_role_cache() -> None:
    _role_cache.clear()


def normalize_role(raw_role: object) -> str:
    if not isinstance(raw_role, str) or not raw_role.strip():
        raise TokenValidationError("Missing valid role")
    role = raw_role.strip().upper()
    if role not in SUPPORTED_ROLES:
        raise TokenValidationError(f"Unsupported role: {role}")
    return role


def _decode_jwt_payload(token: str, settings: Settings) -> dict:
    if not settings.jwt_secret or len(settings.jwt_secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )
    decode_kwargs: dict = {
        "algorithms": [settings.jwt_algorithm],
        "options": {"require": ["sub", "iat", "exp"]},
    }
    if settings.jwt_issuer:
        decode_kwargs["issuer"] = settings.jwt_issuer
        decode_kwargs["options"]["require"].append("iss")
    if settings.jwt_audience:
        decode_kwargs["audience"] = settings.jwt_audience
        decode_kwargs["options"]["require"].append("aud")

    try:
        return jwt.decode(token, settings.jwt_secret, **decode_kwargs)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def _fetch_role_from_auth(
    token: str,
    expected_user_id: uuid.UUID,
    token_exp_ts: float,
    auth_url: str,
) -> str:
    """Resolve user role from Auth service GET /me after local JWT verification."""
    cache_key = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now_mono = time.monotonic()
    cached = _role_cache.get(cache_key)
    if cached and now_mono < cached[0] and cached[1] == expected_user_id:
        return cached[2]

    url = f"{auth_url.rstrip('/')}/me"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from exc

    if response.status_code in (401, 403, 404):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not response.is_success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service error",
        )

    try:
        body = response.json()
        remote_id = uuid.UUID(str(body["id"]))
        if remote_id != expected_user_id:
            raise TokenValidationError("Auth user ID does not match token subject")
        role = normalize_role(body.get("role"))
    except (ValueError, KeyError, TypeError, TokenValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication profile",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    remaining_exp = max(0.0, token_exp_ts - time.time())
    ttl = min(_ROLE_CACHE_TTL_SECONDS, remaining_exp)
    if ttl > 0:
        if len(_role_cache) >= _MAX_CACHE_SIZE:
            _role_cache.clear()
        _role_cache[cache_key] = (now_mono + ttl, expected_user_id, role)
    return role


async def resolve_principal(token: str, settings: Settings) -> Principal:
    """Verify JWT signature/expiry/claims and resolve the authenticated principal's role."""
    payload = _decode_jwt_payload(token, settings)
    try:
        user_id = uuid.UUID(str(payload["sub"]))
        iat = datetime.fromtimestamp(float(payload["iat"]), tz=timezone.utc)
        exp_ts = float(payload["exp"])
        exp = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if "role" in payload:
        try:
            role = normalize_role(payload["role"])
        except TokenValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
    else:
        if not settings.auth_url or not settings.auth_url.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication role lookup is not configured",
            )
        role = await _fetch_role_from_auth(token, user_id, exp_ts, settings.auth_url)

    return Principal(
        user_id=user_id,
        role=role,
        issuer=str(payload["iss"]) if "iss" in payload else None,
        audience=payload.get("aud"),
        issued_at=iat,
        expires_at=exp,
    )
