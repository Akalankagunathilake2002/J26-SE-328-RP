import asyncio
import json
import logging
import sys
import uuid
from datetime import date
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import dispose_engine, get_sessionmaker
from app.models.profiles import (
    IndustryProfile,
    IndustryProfileRequirement,
    IndustrySkillEvidence,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SEED_DIR = BASE_DIR / "seed" / "industry-role-profiles"


# Import a single industry role profile fixture idempotently
async def import_single_profile(session, fixture_path: Path) -> tuple[str, bool, int, int]:
    with open(fixture_path, encoding="utf-8") as f:
        content = json.load(f)

    data = content.get("data", {})
    role_data = data.get("industry_role_profile") or data.get("industryRoleProfile")
    if not role_data:
        raise ValueError(f"No industry_role_profile data block in {fixture_path}")

    role_id = role_data.get("role_id") or role_data.get("roleId")
    candidate_role_id = role_data.get("candidate_role_id") or role_data.get("candidateRoleId")
    profile_version = role_data.get("profile_version") or role_data.get("profileVersion") or "1.0"

    # Check for existing profile with identical role identifier and profile version
    stmt = (
        select(IndustryProfile)
        .options(
            selectinload(IndustryProfile.requirements).selectinload(
                IndustryProfileRequirement.sample_evidence
            )
        )
    )
    if role_id:
        stmt = stmt.where(
            IndustryProfile.role_id == role_id,
            IndustryProfile.profile_version == profile_version,
        )
    elif candidate_role_id:
        stmt = stmt.where(
            IndustryProfile.candidate_role_id == candidate_role_id,
            IndustryProfile.profile_version == profile_version,
        )
    else:
        raise ValueError(f"Fixture {fixture_path} missing both role_id and candidate_role_id")

    res = await session.execute(stmt)
    existing = res.scalars().first()
    if existing is not None:
        req_count = len(existing.requirements)
        ev_count = sum(len(r.sample_evidence) for r in existing.requirements)
        logger.info(
            f"Profile already exists for role_id='{role_id or candidate_role_id}', "
            f"version='{profile_version}' (id={existing.id}). Skipping to prevent duplicates."
        )
        return str(role_id or candidate_role_id), False, req_count, ev_count

    # Construct new IndustryProfile entity
    m_ev = role_data.get("market_evidence", {})
    obs_period = m_ev.get("observation_period", {})
    d_from = obs_period.get("from")
    d_to = obs_period.get("to")
    domain_obj = role_data.get("domain", {})

    profile = IndustryProfile(
        id=uuid.uuid4(),
        role_id=role_id,
        candidate_role_id=candidate_role_id,
        role_name=role_data.get("primary_observed_title", "Target Role"),
        primary_observed_title=role_data.get("primary_observed_title", "Target Role"),
        observed_titles=role_data.get("observed_titles", []),
        mapping_status=role_data.get("mapping_status", "verified"),
        profile_status=role_data.get("profile_status", "active"),
        domain_id=domain_obj.get("domain_id") or domain_obj.get("domainId"),
        domain_name=domain_obj.get("domain_name") or domain_obj.get("domainName"),
        career_level=role_data.get("career_level") or role_data.get("careerLevel", "ENTRY_LEVEL"),
        profile_version=profile_version,
        job_posting_count=m_ev.get("job_posting_count"),
        observation_period_from=date.fromisoformat(d_from) if d_from else None,
        observation_period_to=date.fromisoformat(d_to) if d_to else None,
        source_message_id=content.get("message_id"),
        raw_payload=content,
    )

    reqs_added = 0
    evidence_added = 0

    for item in role_data.get("requirements", []):
        prof_obj = item.get("required_proficiency") or item.get("requiredProficiency", {})
        prof_score = (
            item.get("required_proficiency_score")
            if "required_proficiency_score" in item
            else (
                prof_obj.get("score")
                if isinstance(prof_obj, dict)
                else item.get("requiredProficiencyScore", 0.5)
            )
        )
        prof_level = (
            item.get("required_proficiency_level")
            or (prof_obj.get("level") if isinstance(prof_obj, dict) else None)
            or item.get("requiredProficiencyLevel", "INTERMEDIATE")
        )
        weight = (
            item.get("demand_weight")
            if "demand_weight" in item
            else item.get("DemandWeight", item.get("demandWeight", 1.0))
        )
        d_ev = item.get("demand_evidence", {})

        req = IndustryProfileRequirement(
            id=uuid.uuid4(),
            industry_profile_id=profile.id,
            skill_id=item.get("skill_id") or item.get("skillId"),
            candidate_skill_id=item.get("candidate_skill_id") or item.get("candidateSkillId"),
            standard_name=item.get("standard_name", ""),
            primary_observed_term=item.get("primary_observed_term", item.get("standard_name", "")),
            observed_terms=item.get("observed_terms", []),
            mapping_status=item.get("mapping_status", "verified"),
            skill_type=item.get("skill_type") or item.get("skillType", "TECHNICAL"),
            required_proficiency_level=prof_level,
            required_proficiency_score=float(prof_score) if prof_score is not None else None,
            demand_weight=float(weight),
            demand_frequency=d_ev.get("frequency"),
            job_ads_containing_skill=d_ev.get("job_ads_containing_skill"),
            required_count=d_ev.get("required_count"),
            preferred_count=d_ev.get("preferred_count"),
            mentioned_count=d_ev.get("mentioned_count"),
        )

        for ev in item.get("sample_evidence", []):
            s_date = ev.get("source_date")
            ev_record = IndustrySkillEvidence(
                id=uuid.uuid4(),
                requirement_id=req.id,
                source_id=ev.get("source_id", "SYNTH-001"),
                company=ev.get("company"),
                job_title=ev.get("job_title"),
                source_date=date.fromisoformat(s_date) if s_date else None,
                text_excerpt=ev.get("text_excerpt", ""),
            )
            req.sample_evidence.append(ev_record)
            evidence_added += 1

        profile.requirements.append(req)
        reqs_added += 1

    session.add(profile)
    await session.commit()
    logger.info(
        f"Imported profile for role_id='{role_id or candidate_role_id}': "
        f"{reqs_added} requirements, {evidence_added} evidence records."
    )
    return str(role_id or candidate_role_id), True, reqs_added, evidence_added


# Main runner to import all 3 seed fixtures
async def main():
    if not SEED_DIR.exists():
        logger.error(f"Seed directory not found: {SEED_DIR}")
        sys.exit(1)

    fixture_files = sorted(SEED_DIR.glob("*.json"))
    if len(fixture_files) != 3:
        logger.warning(f"Expected 3 fixtures in {SEED_DIR}, found {len(fixture_files)}")

    session_maker = get_sessionmaker()
    async with session_maker() as session:
        for p in fixture_files:
            logger.info(f"Processing fixture: {p.name}")
            await import_single_profile(session, p)

    await dispose_engine()
    logger.info("Import completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
