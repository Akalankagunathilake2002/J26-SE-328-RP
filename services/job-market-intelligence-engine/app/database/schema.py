"""PostgreSQL tables for the collected job ads (database ``job_market_db``).

    job_ads                 one row per ad: listing details, cleaned text, status, role, flags
    job_ad_sectors          ad ↔ sector (an ad can be listed under several sectors)
    job_ad_skills           every skill mention: raw text, position, extractor, SSKS ID, match type
    job_ad_status_history   every status change (active → expired / removed, and back)
    sync_runs               one row per sync
    role_skill_demand       view: per role, sector and skill, how many active ads ask for it

Nothing is ever deleted: expired and removed ads stay, so trends can be measured. The text columns
hold the cleaned text, with personal data already removed. The same definitions work on SQLite,
which the tests use.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.engine import Engine

metadata = MetaData()

job_ads = Table(
    "job_ads",
    metadata,
    Column("site", String(50), primary_key=True),
    Column("job_id", String(50), primary_key=True),
    Column("url", Text, nullable=False),
    Column("job_title", Text),
    Column("company", Text),  # NULL: "Company Name Withheld"
    Column("location", Text),
    Column("posted_date", Date),
    Column("closing_date", Date),
    Column("employment_type", Text),
    Column("experience_level", Text),
    Column("salary_text", Text),
    Column("description_text", Text),  # cleaned: no e-mails, phone numbers or names
    Column("requirements_text", Text),
    Column("is_image_ad", Boolean, nullable=False),
    Column("status", String(20), nullable=False),  # active | expired | removed
    Column("collected_at", DateTime(timezone=True)),
    Column("last_seen_at", DateTime(timezone=True)),
    Column("status_changed_at", DateTime(timezone=True)),
    Column("role", Text),  # from config/role_taxonomy.yaml, or the cleaned title if unmapped
    Column("role_mapped", Boolean),
    Column("seniority", Text),
    Column("has_text", Boolean),  # False: a banner-only flyer, no skills could be read
    Column("flags", Text),  # comma-separated: banner_only, no_requirements_section, not_agriculture
    Column("loaded_at", DateTime(timezone=True), nullable=False),
)

_ad = (["site", "job_id"], ["job_ads.site", "job_ads.job_id"])

job_ad_sectors = Table(
    "job_ad_sectors",
    metadata,
    Column("site", String(50), primary_key=True),
    Column("job_id", String(50), primary_key=True),
    Column("sector", String(50), primary_key=True),
    ForeignKeyConstraint(*_ad, ondelete="CASCADE"),
)

job_ad_skills = Table(
    "job_ad_skills",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("site", String(50), nullable=False),
    Column("job_id", String(50), nullable=False),
    Column("extractor", String(20), nullable=False),  # lexicon | ner
    Column("raw_text", Text, nullable=False),  # as written in the ad
    Column("start_char", Integer, nullable=False),  # position in the ad text the extractor read
    Column("end_char", Integer, nullable=False),
    Column("label", Text),  # the lexicon category, or the NER label
    Column("lexicon_skill", Text),
    Column("counted_as", Text),  # the skill it counts as in demand; NULL: not counted
    Column("ssk_id", String(50)),  # SSKS ID of the raw text (exact or alias match only)
    Column("ssks_name", Text),
    Column("match_type", String(20), nullable=False),  # exact | alias | fuzzy | unmatched | pending
    ForeignKeyConstraint(*_ad, ondelete="CASCADE"),
    Index("ix_job_ad_skills_ad", "site", "job_id"),
    Index("ix_job_ad_skills_ssk_id", "ssk_id"),
    Index("ix_job_ad_skills_counted_as", "counted_as"),
)

job_ad_status_history = Table(
    "job_ad_status_history",
    metadata,
    Column("site", String(50), primary_key=True),
    Column("job_id", String(50), primary_key=True),
    Column("changed_at", DateTime(timezone=True), primary_key=True),
    Column("status", String(20), primary_key=True),
    ForeignKeyConstraint(*_ad, ondelete="CASCADE"),
)

sync_runs = Table(
    "sync_runs",
    metadata,
    Column("site", String(50), primary_key=True),
    Column("synced_at", DateTime(timezone=True), primary_key=True),
    Column("live_on_homepage", Integer),  # NULL: the homepage was not read or not trusted
    Column("listed", Integer),
    Column("new_ads", Integer),
    Column("active", Integer),
    Column("expired", Integer),
    Column("removed", Integer),
    Column("reactivated", Integer),
    Column("unconfirmed", Integer),
)

# Demand per role, sector and skill over active ads: "ads" asking for the skill, out of
# "ads_with_text" of that role and sector (banner-only flyers left out, as in the skill profile).
ROLE_SKILL_DEMAND = """
CREATE VIEW role_skill_demand AS
WITH active AS (
    SELECT a.site, a.job_id, a.role, s.sector, a.has_text
    FROM job_ads a
    JOIN job_ad_sectors s ON s.site = a.site AND s.job_id = a.job_id
    WHERE a.status = 'active'
),
totals AS (
    SELECT role, sector, COUNT(*) AS ads,
           SUM(CASE WHEN has_text THEN 1 ELSE 0 END) AS ads_with_text
    FROM active
    GROUP BY role, sector
),
demand AS (
    SELECT x.role, x.sector, k.counted_as AS skill,
           COUNT(DISTINCT x.site || ':' || x.job_id) AS ads
    FROM active x
    JOIN job_ad_skills k ON k.site = x.site AND k.job_id = x.job_id
    WHERE k.counted_as IS NOT NULL
    GROUP BY x.role, x.sector, k.counted_as
)
SELECT d.role, d.sector, d.skill, d.ads, t.ads_with_text,
       CASE WHEN t.ads_with_text > 0 THEN 1.0 * d.ads / t.ads_with_text END AS share
FROM demand d
JOIN totals t ON t.role = d.role AND t.sector = d.sector
"""


def create_schema(engine: Engine) -> None:
    """Create the tables if they don't exist, and (re)create the view."""
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP VIEW IF EXISTS role_skill_demand"))
        connection.execute(text(ROLE_SKILL_DEMAND))
