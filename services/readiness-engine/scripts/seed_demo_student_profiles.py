import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import dispose_engine, get_sessionmaker
from app.models.cache import CachedSkill
from app.models.profiles import (
    SkillEvidence,
    UserSkillProfile,
    UserSkillProfileSkill,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SEED_DIR = BASE_DIR / "seed" / "user-skill-profiles"

# Demo student definitions with fixed user IDs and corresponding fixture files
DEMO_STUDENTS = [
    {
        "name": "Software Testing Intern candidate",
        "user_id": uuid.UUID("677add2f-c700-4346-8980-a09c4924c665"),
        "target_role_id": "RL-000003",
        "fixture_file": "user_skill_profile_02.json",
    },
    {
        "name": "Junior Web Developer candidate",
        "user_id": uuid.UUID("1f40007d-6a6c-49ff-b8cc-dea297d258f2"),
        "target_role_id": "RL-000015",
        "fixture_file": "user_skill_profile_01.json",
        "known_profile_id": uuid.UUID("321c7841-c890-4808-a128-9ac119f1d7e1"),
    },
    {
        "name": "Junior Data Analyst candidate",
        "user_id": uuid.UUID("dfad8a0d-0654-4962-84c9-b3eda380a294"),
        "target_role_id": "RL-000017",
        "fixture_file": "user_skill_profile_03.json",
    },
]


# Seed a single student profile idempotently within the active transaction
async def seed_single_student_profile(
    session,
    student_cfg: dict,
    cached_skill_ids: set[str],
) -> dict[str, int]:
    fixture_path = SEED_DIR / student_cfg["fixture_file"]
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

    with open(fixture_path, encoding="utf-8") as f:
        content = json.load(f)

    data = content.get("data", {})
    user_skill_profile_data = data.get("user_skill_profile") or data.get("userSkillProfile")
    if not user_skill_profile_data:
        raise ValueError(f"No user_skill_profile block found in {fixture_path}")

    user_id = student_cfg["user_id"]
    profile_version = (
        user_skill_profile_data.get("profile_version")
        or user_skill_profile_data.get("profileVersion")
        or "1.0"
    )

    stats = {
        "profiles_inserted": 0,
        "profiles_skipped": 0,
        "skills_inserted": 0,
        "skills_skipped": 0,
        "evidence_inserted": 0,
        "evidence_skipped": 0,
        "unresolved_skills": 0,
    }

    # Query for existing profile by user_id and profile_version
    stmt = (
        select(UserSkillProfile)
        .options(
            selectinload(UserSkillProfile.skills).selectinload(
                UserSkillProfileSkill.evidence
            )
        )
        .where(
            UserSkillProfile.user_id == user_id,
            UserSkillProfile.profile_version == profile_version,
        )
    )
    res = await session.execute(stmt)
    existing_profile = res.scalars().first()

    raw_skills = user_skill_profile_data.get("skills", [])

    if existing_profile is not None:
        stats["profiles_skipped"] += 1
        logger.info(
            f"Preserving existing profile for {student_cfg['name']} "
            f"(user_id={user_id}, profile_id={existing_profile.id}). Checking child records."
        )

        existing_skills_by_id = {
            s.skill_id or s.candidate_skill_id: s for s in existing_profile.skills
        }

        for skill_item in raw_skills:
            skill_id = skill_item.get("skill_id")
            candidate_skill_id = skill_item.get("candidate_skill_id")
            lookup_key = skill_id or candidate_skill_id

            if skill_id and skill_id not in cached_skill_ids:
                logger.warning(
                    f"Skill ID {skill_id} ({skill_item.get('standard_name')}) not found in cached_skills."
                )
                stats["unresolved_skills"] += 1

            if lookup_key in existing_skills_by_id:
                stats["skills_skipped"] += 1
                existing_skill = existing_skills_by_id[lookup_key]
                existing_evidence_ids = {e.evidence_id for e in existing_skill.evidence}

                for ev_item in skill_item.get("evidence", []):
                    ev_id = ev_item.get("evidence_id")
                    if ev_id in existing_evidence_ids:
                        stats["evidence_skipped"] += 1
                    else:
                        new_ev = SkillEvidence(
                            id=uuid.uuid4(),
                            user_skill_profile_skill_id=existing_skill.id,
                            evidence_id=ev_id,
                            source_type=ev_item.get("source_type", "PROJECT"),
                            source_name=ev_item.get("source_name", "Demo source"),
                            evidence_type=ev_item.get("evidence_type", "PROJECT_DEMONSTRATED"),
                            excerpt=ev_item.get("excerpt", ""),
                            strength=float(ev_item.get("strength", 0.7)),
                            verified=bool(ev_item.get("verified", False)),
                        )
                        session.add(new_ev)
                        existing_skill.evidence.append(new_ev)
                        stats["evidence_inserted"] += 1
            else:
                prof_obj = skill_item.get("proficiency", {})
                prof_score = (
                    skill_item.get("proficiency_score")
                    if "proficiency_score" in skill_item
                    else (prof_obj.get("score") if isinstance(prof_obj, dict) else 0.5)
                )
                prof_level = (
                    skill_item.get("proficiency_level")
                    or (prof_obj.get("level") if isinstance(prof_obj, dict) else None)
                    or "BEGINNER"
                )
                conf = skill_item.get("evidence_confidence", 0.8)

                new_skill = UserSkillProfileSkill(
                    id=uuid.uuid4(),
                    user_skill_profile_id=existing_profile.id,
                    skill_id=skill_id,
                    candidate_skill_id=candidate_skill_id,
                    standard_name=skill_item.get("standard_name", ""),
                    primary_observed_term=skill_item.get(
                        "primary_observed_term", skill_item.get("standard_name", "")
                    ),
                    observed_terms=skill_item.get("observed_terms", []),
                    mapping_status=skill_item.get("mapping_status", "verified"),
                    skill_type=skill_item.get("skill_type", "TECHNICAL"),
                    proficiency_level=prof_level,
                    proficiency_score=float(prof_score) if prof_score is not None else None,
                    evidence_confidence=float(conf) if conf is not None else None,
                    verification_status=skill_item.get("verification_status", "UNVERIFIED"),
                )

                for ev_item in skill_item.get("evidence", []):
                    new_ev = SkillEvidence(
                        id=uuid.uuid4(),
                        user_skill_profile_skill_id=new_skill.id,
                        evidence_id=ev_item.get("evidence_id"),
                        source_type=ev_item.get("source_type", "PROJECT"),
                        source_name=ev_item.get("source_name", "Demo source"),
                        evidence_type=ev_item.get("evidence_type", "PROJECT_DEMONSTRATED"),
                        excerpt=ev_item.get("excerpt", ""),
                        strength=float(ev_item.get("strength", 0.7)),
                        verified=bool(ev_item.get("verified", False)),
                    )
                    new_skill.evidence.append(new_ev)
                    stats["evidence_inserted"] += 1

                session.add(new_skill)
                existing_profile.skills.append(new_skill)
                stats["skills_inserted"] += 1

        return stats

    # Profile does not exist yet; construct new profile hierarchy
    domain_obj = user_skill_profile_data.get("domain", {})
    profile_quality = user_skill_profile_data.get("profile_quality", {})
    completeness_score = profile_quality.get("completeness_score")

    profile_id = student_cfg.get("known_profile_id") or uuid.uuid4()
    profile = UserSkillProfile(
        id=profile_id,
        user_id=user_id,
        profile_version=profile_version,
        domain_id=domain_obj.get("domain_id") or domain_obj.get("domainId", "DOM-IT"),
        domain_name=domain_obj.get("domain_name") or domain_obj.get("domainName", "Information Technology"),
        completeness_score=float(completeness_score) if completeness_score is not None else None,
        source_message_id=content.get("message_id"),
        raw_payload=content,
        received_at=datetime.now(timezone.utc),
    )

    for skill_item in raw_skills:
        skill_id = skill_item.get("skill_id")
        candidate_skill_id = skill_item.get("candidate_skill_id")

        if skill_id and skill_id not in cached_skill_ids:
            logger.warning(
                f"Skill ID {skill_id} ({skill_item.get('standard_name')}) not found in cached_skills."
            )
            stats["unresolved_skills"] += 1

        prof_obj = skill_item.get("proficiency", {})
        prof_score = (
            skill_item.get("proficiency_score")
            if "proficiency_score" in skill_item
            else (prof_obj.get("score") if isinstance(prof_obj, dict) else 0.5)
        )
        prof_level = (
            skill_item.get("proficiency_level")
            or (prof_obj.get("level") if isinstance(prof_obj, dict) else None)
            or "BEGINNER"
        )
        conf = skill_item.get("evidence_confidence", 0.8)

        skill_record = UserSkillProfileSkill(
            id=uuid.uuid4(),
            user_skill_profile_id=profile.id,
            skill_id=skill_id,
            candidate_skill_id=candidate_skill_id,
            standard_name=skill_item.get("standard_name", ""),
            primary_observed_term=skill_item.get(
                "primary_observed_term", skill_item.get("standard_name", "")
            ),
            observed_terms=skill_item.get("observed_terms", []),
            mapping_status=skill_item.get("mapping_status", "verified"),
            skill_type=skill_item.get("skill_type", "TECHNICAL"),
            proficiency_level=prof_level,
            proficiency_score=float(prof_score) if prof_score is not None else None,
            evidence_confidence=float(conf) if conf is not None else None,
            verification_status=skill_item.get("verification_status", "UNVERIFIED"),
        )

        for ev_item in skill_item.get("evidence", []):
            ev_record = SkillEvidence(
                id=uuid.uuid4(),
                user_skill_profile_skill_id=skill_record.id,
                evidence_id=ev_item.get("evidence_id"),
                source_type=ev_item.get("source_type", "PROJECT"),
                source_name=ev_item.get("source_name", "Demo source"),
                evidence_type=ev_item.get("evidence_type", "PROJECT_DEMONSTRATED"),
                excerpt=ev_item.get("excerpt", ""),
                strength=float(ev_item.get("strength", 0.7)),
                verified=bool(ev_item.get("verified", False)),
            )
            skill_record.evidence.append(ev_record)
            stats["evidence_inserted"] += 1

        profile.skills.append(skill_record)
        stats["skills_inserted"] += 1

    session.add(profile)
    stats["profiles_inserted"] += 1
    logger.info(
        f"Inserted profile for {student_cfg['name']} (user_id={user_id}, profile_id={profile.id}) "
        f"with {len(profile.skills)} skills and {stats['evidence_inserted']} evidence records."
    )
    return stats


# Run the repeatable seeding process across all three demo student profiles
async def run_seed():
    sessionmaker = get_sessionmaker()

    total_stats = {
        "profiles_inserted": 0,
        "profiles_skipped": 0,
        "skills_inserted": 0,
        "skills_skipped": 0,
        "evidence_inserted": 0,
        "evidence_skipped": 0,
        "unresolved_skills": 0,
    }

    try:
        async with sessionmaker() as session:
            # Process all demo student fixtures in a single transaction
            async with session.begin():
                # Load cached canonical skill IDs to validate foreign references
                res = await session.execute(select(CachedSkill.skill_id))
                cached_skill_ids = set(res.scalars().all())
                logger.info(f"Loaded {len(cached_skill_ids)} cached canonical skills from database.")

                for student_cfg in DEMO_STUDENTS:
                    logger.info(f"Processing demo student: {student_cfg['name']}...")
                    stats = await seed_single_student_profile(session, student_cfg, cached_skill_ids)
                    for k, v in stats.items():
                        total_stats[k] += v

        logger.info("\n================ SEEDING SUMMARY ================")
        logger.info(f"Profiles inserted : {total_stats['profiles_inserted']}")
        logger.info(f"Profiles skipped  : {total_stats['profiles_skipped']}")
        logger.info(f"Skills inserted   : {total_stats['skills_inserted']}")
        logger.info(f"Skills skipped    : {total_stats['skills_skipped']}")
        logger.info(f"Evidence inserted : {total_stats['evidence_inserted']}")
        logger.info(f"Evidence skipped  : {total_stats['evidence_skipped']}")
        logger.info(f"Unresolved skills : {total_stats['unresolved_skills']}")
        logger.info("==================================================")
        print("\nSeed completed successfully.")
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(run_seed())
