"""The C01 → C03 contract tables (Skillaro_DB_Contract_v2), as C01 writes them.

On the shared database they are created by infrastructure/neon/setup.sql, with the contract's CHECK and
UNIQUE rules; these definitions only describe the columns, so C01 can write to them and the tests can
create them on SQLite. Table names have no schema: the job_market_svc login's search_path is job_market.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import ARRAY

metadata = MetaData()


def _text_list():
    """text[] on PostgreSQL, JSON on SQLite (tests)."""
    return ARRAY(Text).with_variant(JSON(), "sqlite")


role_profiles = Table(
    "role_profiles", metadata,
    Column("profile_id", Uuid, primary_key=True),
    Column("profile_type", String(10), nullable=False),  # ROLE | VACANCY
    Column("vacancy_id", Uuid),
    Column("role_id", String(50)),
    Column("candidate_role_id", Uuid),
    Column("primary_observed_title", Text, nullable=False),
    Column("observed_titles", _text_list()),
    Column("mapping_status", String(50), nullable=False),
    Column("profile_status", String(20), nullable=False),  # DRAFT | PUBLISHED | ARCHIVED
    Column("profile_version", String(40), nullable=False),
    Column("career_level", String(30)),
    Column("domain_id", String(50)),
    Column("sector", String(50)),
    Column("job_posting_count", Integer),
    Column("ads_with_text", Integer),
    Column("observation_period_from", Date),
    Column("observation_period_to", Date),
    Column("published_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

role_profile_requirements = Table(
    "role_profile_requirements", metadata,
    Column("requirement_id", Uuid, primary_key=True),
    Column("profile_id", Uuid, ForeignKey("role_profiles.profile_id", ondelete="CASCADE"), nullable=False),
    Column("skill_id", String(50)),
    Column("candidate_skill_id", Uuid),
    Column("standard_name", Text, nullable=False),
    Column("primary_observed_term", Text),
    Column("observed_terms", _text_list()),
    Column("mapping_status", String(50), nullable=False),
    Column("skill_type", String(50), nullable=False),
    Column("importance", String(20)),
    Column("demand_weight", Numeric(5, 4), nullable=False),
    Column("demand_frequency", Numeric(5, 4)),
    Column("job_ads_containing_skill", Integer),
    Column("required_proficiency_level", String(20)),
    Column("required_proficiency_score", Numeric(5, 4)),
)

role_profile_education = Table(
    "role_profile_education", metadata,
    Column("education_req_id", Uuid, primary_key=True),
    Column("profile_id", Uuid, ForeignKey("role_profiles.profile_id", ondelete="CASCADE"), nullable=False),
    Column("qualification_level", String(40), nullable=False),
    Column("accepted_fields", _text_list()),
    Column("completion_requirement", String(30)),
    Column("is_mandatory", Boolean),
    Column("job_ads_count", Integer),
)

role_profile_experience = Table(
    "role_profile_experience", metadata,
    Column("experience_req_id", Uuid, primary_key=True),
    Column("profile_id", Uuid, ForeignKey("role_profiles.profile_id", ondelete="CASCADE"), nullable=False),
    Column("minimum_years", Numeric(4, 1)),
    Column("relevant_experience_required", Boolean),
    Column("accepted_experience_types", _text_list()),
    Column("job_ads_count", Integer),
)

role_profile_certifications = Table(
    "role_profile_certifications", metadata,
    Column("certification_req_id", Uuid, primary_key=True),
    Column("profile_id", Uuid, ForeignKey("role_profiles.profile_id", ondelete="CASCADE"), nullable=False),
    Column("certification_name", Text, nullable=False),
    Column("issuing_organization", Text),
    Column("is_mandatory", Boolean),
    Column("job_ads_count", Integer),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

requirement_evidence = Table(
    "requirement_evidence", metadata,
    Column("requirement_id", Uuid, ForeignKey("role_profile_requirements.requirement_id", ondelete="CASCADE"),
           primary_key=True),
    Column("site", String(50), primary_key=True),
    Column("job_id", String(50), primary_key=True),
    Column("text_excerpt", Text),
)

CHILD_TABLES = (role_profile_requirements, role_profile_education, role_profile_experience,
                role_profile_certifications)
