import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.algorithms.matching import AliasInput, RelationshipInput
from app.models.cache import CachedAlias, CachedRelationship, KnowledgeSnapshot
from app.models.profiles import (
    IndustryProfile,
    IndustryProfileRequirement,
    UserSkillProfile,
    UserSkillProfileSkill,
)

SEED_DIR = Path(__file__).resolve().parents[2] / "seed"


# Raised when a required student or industry profile is not found in the database
class ProfileNotFoundError(ValueError):
    def __init__(
        self,
        message: str,
        profile_type: str | None = None,
        identifier: Any = None,
    ):
        super().__init__(message)
        self.profile_type = profile_type
        self.identifier = identifier


# Raised when a required or active knowledge snapshot is not found in the database
class SnapshotNotFoundError(ValueError):
    def __init__(self, message: str, snapshot_id: Any = None):
        super().__init__(message)
        self.snapshot_id = snapshot_id


# Parse user profile from disk synchronously to avoid blocking async event loop
def _read_user_fixture(fixture_path: Path) -> dict[str, Any]:
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


# Parse industry profiles from disk synchronously
def _read_industry_fixtures(
    seed_dir: Path, role_id: str | None
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    for file_path in (seed_dir / "industry-role-profiles").glob("*.json"):
        with open(file_path, encoding="utf-8") as f:
            content = json.load(f)
        role_profile = content.get("data", {}).get(
            "industry_role_profile",
            content.get("data", {}).get("industryRoleProfile", {}),
        )
        current_role_id = role_profile.get("role_id") or role_profile.get("roleId")
        current_candidate_id = (
            role_profile.get("candidate_role_id")
            or role_profile.get("candidate_roleId")
            or role_profile.get("candidateRoleId")
        )
        if (
            role_id is None
            or current_role_id == role_id
            or current_candidate_id == role_id
        ):
            return content, role_profile
    return None


# Import a user skill profile from disk fixture into the database
async def import_user_skill_profile_from_fixture(
    session: AsyncSession,
    fixture_path: Path | None = None,
    user_id: uuid.UUID | None = None,
    profile_id: uuid.UUID | None = None,
) -> UserSkillProfile:
    path = fixture_path or (
        SEED_DIR / "user-skill-profiles" / "user_skill_profile_01.json"
    )
    if not path.exists():
        raise FileNotFoundError(f"User skill profile fixture not found: {path}")

    data = _read_user_fixture(path)
    user_data = data.get("data", {}).get(
        "user_skill_profile", data.get("data", {}).get("userSkillProfile", {})
    )
    raw_user_id = user_data.get("user_id") or user_data.get("userId")
    resolved_user_id = (
        user_id
        or (uuid.UUID(str(raw_user_id)) if raw_user_id else None)
        or uuid.UUID("1f40007d-6a6c-49ff-b8cc-dea297d258f2")
    )
    domain_obj = user_data.get("domain", {})
    created_profile = UserSkillProfile(
        id=profile_id or uuid.uuid4(),
        user_id=resolved_user_id,
        profile_version=user_data.get("profile_version")
        or user_data.get("profileVersion", "2026-10-17T20:45:00Z"),
        domain_id=domain_obj.get("domain_id") or domain_obj.get("domainId", "DOM-IT"),
        domain_name=domain_obj.get("domain_name")
        or domain_obj.get("domainName", "Information Technology"),
        source_message_id=data.get("message_id", "FIXTURE-MSG-C02"),
        raw_payload=data,
    )

    for item in user_data.get("skills", []):
        prof_obj = item.get("proficiency", {})
        prof_score = (
            item.get("proficiency_score")
            if "proficiency_score" in item
            else (
                prof_obj.get("score")
                if isinstance(prof_obj, dict)
                else item.get("proficiencyScore", 0.5)
            )
        )
        prof_level = (
            item.get("proficiency_level")
            or (prof_obj.get("level") if isinstance(prof_obj, dict) else None)
            or item.get("proficiencyLevel", "INTERMEDIATE")
        )
        conf = (
            item.get("evidence_confidence")
            if "evidence_confidence" in item
            else item.get("evidenceConfidence", 1.0)
        )
        skill_entry = UserSkillProfileSkill(
            id=uuid.uuid4(),
            skill_id=item.get("skill_id") or item.get("skillId"),
            candidate_skill_id=item.get("candidate_skill_id")
            or item.get("candidateSkillId"),
            standard_name=item.get("standard_name", ""),
            primary_observed_term=item.get(
                "primary_observed_term", item.get("standard_name", "")
            ),
            observed_terms=item.get("observed_terms", []),
            mapping_status=item.get("mapping_status", "verified"),
            skill_type=item.get("skill_type") or item.get("skillType", "TECHNICAL"),
            proficiency_level=prof_level,
            proficiency_score=float(prof_score),
            evidence_confidence=float(conf),
            verification_status=item.get("verification_status")
            or item.get("verificationStatus", "VERIFIED"),
        )
        created_profile.skills.append(skill_entry)

    session.add(created_profile)
    await session.flush()
    return created_profile


# Import an industry role profile from disk fixture into the database
async def import_industry_profile_from_fixture(
    session: AsyncSession,
    role_id: str | None = None,
    profile_id: uuid.UUID | None = None,
    seed_dir: Path | None = None,
) -> IndustryProfile:
    dir_path = seed_dir or SEED_DIR
    matched_data = _read_industry_fixtures(dir_path, role_id)
    if matched_data is None:
        raise FileNotFoundError(
            f"Industry role profile fixture not found for role_id '{role_id}' in {dir_path}"
        )

    full_payload, r_data = matched_data
    domain_obj = r_data.get("domain", {})
    created_role = IndustryProfile(
        id=profile_id or uuid.uuid4(),
        role_id=r_data.get("role_id") or r_data.get("roleId"),
        candidate_role_id=(
            r_data.get("candidate_role_id")
            or r_data.get("candidate_roleId")
            or r_data.get("candidateRoleId")
        ),
        role_name=r_data.get("primary_observed_title", "Target Role"),
        primary_observed_title=r_data.get("primary_observed_title", "Target Role"),
        observed_titles=r_data.get("observed_titles", []),
        mapping_status=r_data.get("mapping_status", "verified"),
        career_level=r_data.get("career_level")
        or r_data.get("careerLevel", "ENTRY_LEVEL"),
        profile_version=r_data.get("profile_version")
        or r_data.get("profileVersion", "2026-10-17T20:00:00Z"),
        domain_id=domain_obj.get("domain_id") or domain_obj.get("domainId", "DOM-IT"),
        domain_name=domain_obj.get("domain_name")
        or domain_obj.get("domainName", "Information Technology"),
        source_message_id=full_payload.get("message_id", "FIXTURE-MSG-C01"),
        raw_payload=full_payload,
    )

    for item in r_data.get("requirements", []):
        req_prof = item.get("required_proficiency") or item.get(
            "requiredProficiency", {}
        )
        prof_score = (
            item.get("required_proficiency_score")
            if "required_proficiency_score" in item
            else (
                req_prof.get("score")
                if isinstance(req_prof, dict)
                else item.get("requiredProficiencyScore", 0.5)
            )
        )
        prof_level = (
            item.get("required_proficiency_level")
            or (req_prof.get("level") if isinstance(req_prof, dict) else None)
            or item.get("requiredProficiencyLevel", "INTERMEDIATE")
        )
        weight = (
            item.get("demand_weight")
            if "demand_weight" in item
            else item.get("DemandWeight", item.get("demandWeight", 1.0))
        )
        req_entry = IndustryProfileRequirement(
            id=uuid.uuid4(),
            skill_id=item.get("skill_id") or item.get("skillId"),
            candidate_skill_id=item.get("candidate_skill_id")
            or item.get("candidateSkillId"),
            standard_name=item.get("standard_name", ""),
            primary_observed_term=item.get(
                "primary_observed_term", item.get("standard_name", "")
            ),
            observed_terms=item.get("observed_terms", []),
            mapping_status=item.get("mapping_status", "verified"),
            skill_type=item.get("skill_type") or item.get("skillType", "TECHNICAL"),
            required_proficiency_level=prof_level,
            required_proficiency_score=float(prof_score),
            demand_weight=float(weight),
        )
        created_role.requirements.append(req_entry)

    session.add(created_role)
    await session.flush()
    return created_role


# Load student skill profile directly from the database without automatic seeding
async def resolve_user_profile(
    session: AsyncSession,
    profile_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    allow_fixture_fallback: bool = False,
) -> UserSkillProfile:
    if profile_id is None and user_id is None:
        raise ProfileNotFoundError(
            "Ambiguous profile selection: either 'profile_id' or 'user_id' must be specified",
            profile_type="user_skill_profile",
        )

    stmt = select(UserSkillProfile).options(selectinload(UserSkillProfile.skills))

    if profile_id is not None:
        stmt = stmt.where(UserSkillProfile.id == profile_id)
    else:
        stmt = stmt.where(UserSkillProfile.user_id == user_id).order_by(
            UserSkillProfile.received_at.desc()
        )

    result = await session.execute(stmt)
    profile = result.scalars().first()
    if profile is not None:
        return profile

    target = f"profile_id={profile_id}" if profile_id else f"user_id={user_id}"
    raise ProfileNotFoundError(
        f"User skill profile could not be resolved from database ({target})",
        profile_type="user_skill_profile",
        identifier=str(profile_id or user_id),
    )


# Load industry role profile directly from the database without automatic seeding
async def resolve_industry_profile(
    session: AsyncSession,
    profile_id: uuid.UUID | None = None,
    role_id: str | None = None,
    allow_fixture_fallback: bool = False,
) -> IndustryProfile:
    if profile_id is None and role_id is None:
        raise ProfileNotFoundError(
            "Ambiguous profile selection: either 'profile_id' or 'role_id' must be specified",
            profile_type="industry_profile",
        )

    stmt = select(IndustryProfile).options(selectinload(IndustryProfile.requirements))

    if profile_id is not None:
        stmt = stmt.where(IndustryProfile.id == profile_id)
    else:
        stmt = stmt.where(
            (IndustryProfile.role_id == role_id)
            | (IndustryProfile.candidate_role_id == role_id)
        ).order_by(IndustryProfile.received_at.desc())

    result = await session.execute(stmt)
    profile = result.scalars().first()
    if profile is not None:
        return profile

    target = f"profile_id={profile_id}" if profile_id else f"role_id={role_id}"
    raise ProfileNotFoundError(
        f"Industry role profile could not be resolved from database ({target})",
        profile_type="industry_profile",
        identifier=str(profile_id or role_id),
    )


# Load knowledge snapshot from database without fallback creation
async def resolve_snapshot(
    session: AsyncSession,
    snapshot_id: uuid.UUID | None = None,
    allow_fixture_fallback: bool = False,
) -> KnowledgeSnapshot:
    stmt = select(KnowledgeSnapshot)
    if snapshot_id is not None:
        stmt = stmt.where(KnowledgeSnapshot.snapshot_id == snapshot_id)
    else:
        stmt = stmt.where(KnowledgeSnapshot.is_active.is_(True)).order_by(
            KnowledgeSnapshot.generated_at.desc()
        )

    result = await session.execute(stmt)
    snapshot = result.scalars().first()
    if snapshot is not None:
        return snapshot

    target = f"snapshot_id={snapshot_id}" if snapshot_id else "active"
    raise SnapshotNotFoundError(
        f"Knowledge snapshot could not be found in database ({target})",
        snapshot_id=str(snapshot_id or "active"),
    )


# Query cached aliases and relationships from the active snapshot
async def load_snapshot_knowledge(
    session: AsyncSession,
    snapshot_id: uuid.UUID,
) -> tuple[list[AliasInput], list[RelationshipInput]]:
    alias_stmt = select(CachedAlias).where(CachedAlias.snapshot_id == snapshot_id)
    alias_res = await session.execute(alias_stmt)
    db_aliases = alias_res.scalars().all()

    rel_stmt = select(CachedRelationship).where(
        CachedRelationship.snapshot_id == snapshot_id
    )
    rel_res = await session.execute(rel_stmt)
    db_rels = rel_res.scalars().all()

    aliases = [
        AliasInput(
            alias_id=a.alias_id,
            skill_id=a.skill_id,
            alias_text=a.alias_text,
            normalized_alias=a.normalized_alias,
        )
        for a in db_aliases
    ]

    relationships = [
        RelationshipInput(
            relationship_id=r.relationship_id,
            source_skill_id=r.source_skill_id,
            target_skill_id=r.target_skill_id,
            relationship_type=r.relationship_type,
            verification_status=r.verification_status,
            evidence_note=r.evidence_note,
        )
        for r in db_rels
    ]

    return aliases, relationships
