"""Who is calling: the Auth Service checks the caller's access token (GET /auth/me).

C01 doesn't share the Auth Service's JWT secret: it forwards the Bearer token to SKILLBRIDGE_AUTH_URL/me and
uses the user it gets back (id, name, email, role). Answers are kept for a short while, so a page that makes
several requests checks the token once.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass

import requests
from fastapi import Header, HTTPException, status

from app.collectors.config import load_settings

CACHE_SECONDS = 30.0
STUDENT, COMPANY, ADMIN = "user", "hr", "admin"  # auth.users roles


@dataclass(frozen=True)
class Caller:
    id: uuid.UUID
    full_name: str
    email: str
    role: str


class AuthUnavailable(Exception):
    pass


_cache: dict[str, tuple[float, Caller | None]] = {}
_lock = threading.Lock()


def caller_from_token(token: str, auth_url: str, session: requests.Session | None = None) -> Caller | None:
    """The user the token belongs to; None for a missing, expired or unknown token."""
    now = time.monotonic()
    with _lock:
        hit = _cache.get(token)
        if hit and now - hit[0] < CACHE_SECONDS:
            return hit[1]
    try:
        response = (session or requests).get(f"{auth_url}/me", headers={"Authorization": f"Bearer {token}"}, timeout=10)
    except requests.RequestException as exc:
        raise AuthUnavailable(str(exc)) from exc
    if response.status_code in (401, 403, 404):
        caller = None
    elif response.ok:
        body = response.json()
        caller = Caller(uuid.UUID(body["id"]), body.get("full_name") or "", body["email"], body.get("role") or STUDENT)
    else:
        raise AuthUnavailable(f"auth service answered {response.status_code}")
    with _lock:
        if len(_cache) > 1000:
            _cache.clear()
        _cache[token] = (now, caller)
    return caller


def current_caller(authorization: str | None = Header(default=None)) -> Caller:
    """FastAPI dependency: the logged-in caller, or 401."""
    auth_url = load_settings().auth_url
    if not auth_url:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Company job posts need SKILLBRIDGE_AUTH_URL")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Log in first", headers={"WWW-Authenticate": "Bearer"})
    try:
        caller = caller_from_token(token.strip(), auth_url)
    except AuthUnavailable:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The sign-in service can't be reached") from None
    if caller is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session has ended. Log in again.",
                            headers={"WWW-Authenticate": "Bearer"})
    return caller


def require_role(caller: Caller, *roles: str) -> None:
    if caller.role not in roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your account can't do this")


def clear_cache() -> None:
    with _lock:
        _cache.clear()
