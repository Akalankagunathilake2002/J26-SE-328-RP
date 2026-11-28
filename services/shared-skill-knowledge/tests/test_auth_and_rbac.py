from datetime import datetime, timedelta, timezone
import uuid

import httpx
import jwt as pyjwt
import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.settings import get_settings
from app.core.security import clear_role_cache
from app.main import app, lifespan
from app.models.aliases import RoleAlias, SkillAlias
from app.models.core import Domain, Role, Skill
from app.models.relationships import SkillRelationship
from tests.conftest import (
    ADMIN_UUID,
    HR_UUID,
    USER_UUID,
    TestingSessionLocal,
    make_jwt,
)


@pytest.mark.anyio
async def test_health_probe_allows_unauthenticated_access(client: AsyncClient):
    res = await client.get("/ssks/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy", "service": "shared-skill-knowledge"}


@pytest.mark.anyio
async def test_jwt_validation_failures_return_401(client: AsyncClient):
    # Missing Authorization header
    assert (await client.get("/ssks/skills/")).status_code == 401
    # Spoofed legacy identity headers without Bearer JWT
    assert (
        await client.get(
            "/ssks/skills/",
            headers={"X-Reviewer-Id": str(ADMIN_UUID), "X-User-Id": str(ADMIN_UUID)},
        )
    ).status_code == 401
    # Malformed token
    assert (
        await client.get("/ssks/skills/", headers={"Authorization": "Bearer not-a-jwt"})
    ).status_code == 401
    # Wrong signature
    bad_sig = make_jwt(role="ADMIN", secret="wrong-secret-that-is-at-least-32-chars-long")
    assert (
        await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {bad_sig}"})
    ).status_code == 401
    # Expired token
    expired = make_jwt(role="ADMIN", expires_delta=timedelta(minutes=-5))
    assert (
        await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {expired}"})
    ).status_code == 401
    # Missing required claims
    no_iat = make_jwt(role="ADMIN", include_iat=False)
    assert (
        await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {no_iat}"})
    ).status_code == 401
    no_exp = make_jwt(role="ADMIN", include_exp=False)
    assert (
        await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {no_exp}"})
    ).status_code == 401
    no_sub = make_jwt(role="ADMIN", include_sub=False)
    assert (
        await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {no_sub}"})
    ).status_code == 401
    # Non-UUID subject
    bad_sub = make_jwt(role="ADMIN", user_id="not-a-uuid")
    assert (
        await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {bad_sub}"})
    ).status_code == 401
    # Unsupported role
    bad_role = make_jwt(role="SUPERUSER")
    assert (
        await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {bad_role}"})
    ).status_code == 401


@pytest.mark.anyio
async def test_optional_issuer_and_audience_enforced_when_configured(client: AsyncClient, monkeypatch):
    monkeypatch.setenv("JWT_ISSUER", "skillaro-auth")
    monkeypatch.setenv("JWT_AUDIENCE", "skillaro-services")
    get_settings.cache_clear()
    try:
        bad_iss = make_jwt(role="USER", issuer="rogue-issuer", audience="skillaro-services")
        assert (
            await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {bad_iss}"})
        ).status_code == 401

        bad_aud = make_jwt(role="USER", issuer="skillaro-auth", audience="other-service")
        assert (
            await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {bad_aud}"})
        ).status_code == 401

        good = make_jwt(role="USER", issuer="skillaro-auth", audience="skillaro-services")
        assert (
            await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {good}"})
        ).status_code == 200
    finally:
        monkeypatch.delenv("JWT_ISSUER", raising=False)
        monkeypatch.delenv("JWT_AUDIENCE", raising=False)
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_original_auth_jwt_contract_without_role_iss_aud_works_via_auth_me(
    client: AsyncClient, monkeypatch
):
    """Verify tokens matching original auth-service ({sub, iat, exp}) enforce RBAC via /auth/me."""
    clear_role_cache()
    settings = get_settings()
    now = datetime.now(timezone.utc)

    def make_original_auth_token(uid: uuid.UUID, exp_delta: timedelta = timedelta(minutes=60)) -> str:
        # Exact payload structure emitted by services/auth-service/app/core/security.py
        return pyjwt.encode(
            {"sub": str(uid), "iat": now, "exp": now + exp_delta},
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

    role_directory = {
        str(USER_UUID): "user",
        str(HR_UUID): "hr",
        str(ADMIN_UUID): "admin",
    }

    def auth_me_handler(request: httpx.Request) -> httpx.Response:
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ").strip()
        try:
            payload = pyjwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            uid = str(uuid.UUID(payload["sub"]))
        except Exception:
            return httpx.Response(401, json={"detail": "Not authenticated"})
        role = role_directory.get(uid)
        if not role:
            return httpx.Response(401, json={"detail": "Not authenticated"})
        return httpx.Response(
            200,
            json={"id": uid, "full_name": "Test User", "email": "u@example.com", "role": role},
        )

    real_async_client = httpx.AsyncClient

    class MockAuthAsyncClient:
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(auth_me_handler)
            self._inner = real_async_client(*args, **kwargs)

        async def __aenter__(self):
            return await self._inner.__aenter__()

        async def __aexit__(self, *args):
            return await self._inner.__aexit__(*args)

    # Without AUTH_URL configured, a token lacking a role claim must fail closed (503) rather than invent a role.
    user_tok = make_original_auth_token(USER_UUID)
    assert (
        await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {user_tok}"})
    ).status_code == 503

    monkeypatch.setenv("AUTH_URL", "http://auth-service:8006/auth")
    get_settings.cache_clear()
    monkeypatch.setattr("app.core.security.httpx.AsyncClient", MockAuthAsyncClient)

    try:
        hr_tok = make_original_auth_token(HR_UUID)
        admin_tok = make_original_auth_token(ADMIN_UUID)

        # 1. Original Auth user token can read skills, but gets 403 on HR/ADMIN endpoints
        assert (
            await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {user_tok}"})
        ).status_code == 200
        assert (
            await client.post(
                "/ssks/skills/",
                headers={"Authorization": f"Bearer {user_tok}"},
                json={"preferred_name": "Go", "skill_type": "PROGRAMMING_LANGUAGE"},
            )
        ).status_code == 403
        assert (
            await client.get("/ssks/candidates/entities", headers={"Authorization": f"Bearer {user_tok}"})
        ).status_code == 403

        # 2. Original Auth hr token can submit/review candidates, gets 403 on admin taxonomy writes
        cand_res = await client.post(
            "/ssks/candidates/entities",
            headers={"Authorization": f"Bearer {hr_tok}"},
            json={
                "entity_type": "SKILL",
                "submitted_name": "GraphQL",
                "proposed_skill_type": "SOFTWARE_OR_TOOL",
            },
        )
        assert cand_res.status_code == 201
        cand_id = cand_res.json()["candidate_entity_id"]

        rev_res = await client.patch(
            f"/ssks/candidates/entities/{cand_id}/review",
            headers={"Authorization": f"Bearer {hr_tok}"},
            json={"action": "APPROVE"},
        )
        assert rev_res.status_code == 200
        assert rev_res.json()["reviewed_by"] == str(HR_UUID)

        assert (
            await client.post(
                "/ssks/skills/",
                headers={"Authorization": f"Bearer {hr_tok}"},
                json={"preferred_name": "Zig", "skill_type": "PROGRAMMING_LANGUAGE"},
            )
        ).status_code == 403

        # 3. Original Auth admin token can create canonical skills and access admin/service endpoints
        sk_res = await client.post(
            "/ssks/skills/",
            headers={"Authorization": f"Bearer {admin_tok}"},
            json={"preferred_name": "Zig", "skill_type": "PROGRAMMING_LANGUAGE"},
        )
        assert sk_res.status_code == 201
        assert (
            await client.get("/ssks/embeddings/skills", headers={"Authorization": f"Bearer {admin_tok}"})
        ).status_code == 200

        # 4. Unknown user / expired original Auth token rejected with 401
        unknown_tok = make_original_auth_token(uuid.uuid4())
        assert (
            await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {unknown_tok}"})
        ).status_code == 401

        expired_tok = make_original_auth_token(USER_UUID, exp_delta=timedelta(minutes=-1))
        assert (
            await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {expired_tok}"})
        ).status_code == 401
    finally:
        clear_role_cache()
        monkeypatch.delenv("AUTH_URL", raising=False)
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_lowercase_role_claims_from_auth_service_are_accepted(client: AsyncClient):
    user_token = make_jwt(role="user", user_id=USER_UUID)
    hr_token = make_jwt(role="hr", user_id=HR_UUID)
    admin_token = make_jwt(role="admin", user_id=ADMIN_UUID)

    assert (
        await client.get("/ssks/skills/", headers={"Authorization": f"Bearer {user_token}"})
    ).status_code == 200
    assert (
        await client.get("/ssks/candidates/entities", headers={"Authorization": f"Bearer {hr_token}"})
    ).status_code == 200
    assert (
        await client.post(
            "/ssks/domains/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"code": "SEC", "name": "Security"},
        )
    ).status_code == 201


@pytest.mark.anyio
async def test_unconfigured_jwt_secret_fails_closed(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "")
    get_settings.cache_clear()
    try:
        token = make_jwt(role="ADMIN", secret="some-secret-that-is-over-32-characters-long")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            res = await c.get("/ssks/skills/", headers={"Authorization": f"Bearer {token}"})
            assert res.status_code == 503
    finally:
        monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-at-least-32-characters-long")
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_rbac_matrix_across_user_hr_service_admin(
    client: AsyncClient, user_headers, hr_headers, service_headers, admin_headers
):
    async with TestingSessionLocal() as session:
        session.add(Domain(domain_id="DOM-IT", code="IT", name="IT"))
        session.add(Skill(skill_id="SK-1", preferred_name="Python", skill_type="PROGRAMMING_LANGUAGE"))
        session.add(Skill(skill_id="SK-2", preferred_name="FastAPI", skill_type="SOFTWARE_OR_TOOL"))
        session.add(Role(role_id="RL-1", preferred_name="Backend Engineer"))
        await session.flush()
        session.add(
            SkillAlias(
                alias_id=uuid.uuid4(),
                skill_id="SK-1",
                alias_text="Py3",
                normalized_alias="py3",
                verification_status="VERIFIED",
            )
        )
        session.add(
            SkillAlias(
                alias_id=uuid.uuid4(),
                skill_id="SK-1",
                alias_text="PyLang",
                normalized_alias="pylang",
                verification_status="UNVERIFIED",
            )
        )
        session.add(
            RoleAlias(
                alias_id=uuid.uuid4(),
                role_id="RL-1",
                alias_text="BE Dev",
                normalized_alias="be dev",
                verification_status="UNVERIFIED",
            )
        )
        session.add(
            SkillRelationship(
                relationship_id=uuid.uuid4(),
                source_skill_id="SK-2",
                target_skill_id="SK-1",
                relationship_type="PREREQUISITE_OF",
                verification_status="VERIFIED",
            )
        )
        session.add(
            SkillRelationship(
                relationship_id=uuid.uuid4(),
                source_skill_id="SK-1",
                target_skill_id="SK-2",
                relationship_type="RELATED_TO",
                verification_status="UNVERIFIED",
            )
        )
        await session.commit()

    for hdrs in (user_headers, service_headers):
        assert (await client.get("/ssks/skills/", headers=hdrs)).status_code == 200
        assert (await client.get("/ssks/roles/", headers=hdrs)).status_code == 200
        assert (await client.get("/ssks/domains/", headers=hdrs)).status_code == 200
        assert (await client.get("/ssks/sources", headers=hdrs)).status_code == 200
        assert (await client.get("/ssks/skills/SK-1/external-ids", headers=hdrs)).status_code == 200
        assert (
            await client.post("/ssks/normalize/skills", headers=hdrs, json={"items": ["Python"]})
        ).status_code == 200

        rels = await client.get("/ssks/relationships", headers=hdrs)
        assert rels.status_code == 200
        assert all(r["verification_status"] == "VERIFIED" for r in rels.json())
        assert (
            await client.get("/ssks/relationships?verification_status=UNVERIFIED", headers=hdrs)
        ).status_code == 403

        s_aliases = await client.get("/ssks/skills/SK-1/aliases", headers=hdrs)
        assert s_aliases.status_code == 200
        assert [a["alias_text"] for a in s_aliases.json()] == ["Py3"]
        assert (
            await client.get("/ssks/skills/SK-1/aliases?verification_status=UNVERIFIED", headers=hdrs)
        ).status_code == 403

    assert (
        await client.post(
            "/ssks/candidates/entities",
            headers=user_headers,
            json={"entity_type": "SKILL", "submitted_name": "Go", "proposed_skill_type": "PROGRAMMING_LANGUAGE"},
        )
    ).status_code == 403
    assert (await client.get("/ssks/candidates/entities", headers=user_headers)).status_code == 403
    assert (
        await client.post(
            "/ssks/candidates/relationships",
            headers=user_headers,
            json={"source_skill_id": "SK-1", "target_skill_id": "SK-2", "proposed_relationship_type": "RELATED_TO"},
        )
    ).status_code == 403
    assert (await client.get("/ssks/candidates/relationships", headers=user_headers)).status_code == 403
    assert (await client.get("/ssks/embeddings/skills", headers=user_headers)).status_code == 403
    assert (
        await client.post(
            "/ssks/skills/",
            headers=user_headers,
            json={"preferred_name": "Go", "skill_type": "PROGRAMMING_LANGUAGE"},
        )
    ).status_code == 403

    assert (
        await client.get("/ssks/skills/SK-1/aliases?verification_status=UNVERIFIED", headers=hr_headers)
    ).status_code == 200
    assert (
        await client.get("/ssks/relationships?verification_status=UNVERIFIED", headers=hr_headers)
    ).status_code == 200
    assert (await client.get("/ssks/embeddings/skills", headers=hr_headers)).status_code == 403
    assert (
        await client.post(
            "/ssks/skills/",
            headers=hr_headers,
            json={"preferred_name": "Rust", "skill_type": "PROGRAMMING_LANGUAGE"},
        )
    ).status_code == 403
    assert (
        await client.patch("/ssks/skills/SK-1", headers=hr_headers, json={"description": "blocked"})
    ).status_code == 403
    assert (await client.post("/ssks/skills/SK-1/retire", headers=hr_headers)).status_code == 403
    assert (
        await client.post("/ssks/skills/SK-1/aliases", headers=hr_headers, json={"alias_text": "Blocked"})
    ).status_code == 403
    assert (
        await client.post(
            "/ssks/relationships",
            headers=hr_headers,
            json={"source_skill_id": "SK-1", "target_skill_id": "SK-2", "relationship_type": "PART_OF"},
        )
    ).status_code == 403

    svc_cand = await client.post(
        "/ssks/candidates/entities",
        headers=service_headers,
        json={"entity_type": "SKILL", "submitted_name": "Terraform", "proposed_skill_type": "SOFTWARE_OR_TOOL"},
    )
    assert svc_cand.status_code == 201
    svc_cand_id = svc_cand.json()["candidate_entity_id"]
    assert (await client.get("/ssks/candidates/entities", headers=service_headers)).status_code == 403
    assert (
        await client.patch(
            f"/ssks/candidates/entities/{svc_cand_id}/review",
            headers=service_headers,
            json={"action": "APPROVE"},
        )
    ).status_code == 403
    assert (
        await client.post(
            f"/ssks/candidates/entities/{svc_cand_id}/merge-as-alias",
            headers=hr_headers,
            json={"target_entity_id": "SK-1"},
        )
    ).status_code == 403
    assert (await client.get("/ssks/embeddings/skills", headers=service_headers)).status_code == 200
    assert (
        await client.put(
            "/ssks/embeddings/skills/SK-1",
            headers=service_headers,
            json={"embedding_model": "m", "embedding_text_hash": "a" * 64, "embedding": [0.1] * 384},
        )
    ).status_code == 403

    assert (
        await client.put(
            "/ssks/embeddings/skills/SK-1",
            headers=admin_headers,
            json={"embedding_model": "m", "embedding_text_hash": "a" * 64, "embedding": [0.1] * 384},
        )
    ).status_code == 200
    assert (await client.get("/ssks/embeddings/skills/SK-1", headers=service_headers)).status_code == 200


@pytest.mark.anyio
async def test_startup_lifespan_does_not_create_or_alter_schema(tmp_path, monkeypatch):
    db_file = tmp_path / "empty_startup.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_file.as_posix()}")
    get_settings.cache_clear()
    try:
        async with lifespan(app):
            pass
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_file.as_posix()}")
        async with engine.connect() as conn:
            rows = await conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = rows.fetchall()
        await engine.dispose()
        assert tables == []
    finally:
        get_settings.cache_clear()
