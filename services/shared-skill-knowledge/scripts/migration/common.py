"""Shared configuration, UUIDv5 mapping, CSV I/O, and safe DSN helpers for SSKS migration."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SERVICE_ROOT.parents[1]

PROTECTED_IMPORT_READY_DIR = (SERVICE_ROOT / "seed" / "import_ready").resolve()
LEGACY_NEON_SEED_DIR = (SERVICE_ROOT / "seed" / "ssks_neon_import").resolve()
DEFAULT_EXPORT_DIR = (LEGACY_NEON_SEED_DIR / "exports" / "current_ssks_db").resolve()
DEFAULT_INFRA_ENV = REPO_ROOT / "infrastructure" / ".env"

# Fixed namespace so legacy-to-UUIDv5 conversions are deterministic across runs and environments.
SSKS_UUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "ssks.skillaro.v2")

NULL_MARKER = "\\N"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
EXPECTED_EMBEDDING_DIMENSION = 384
EMBEDDING_TEXT_METHOD = "preferred_name + '. ' + description (or preferred_name when description is empty)"

LEGACY_TABLES = [
    "domains",
    "knowledge_sources",
    "skills",
    "roles",
    "skill_domains",
    "role_domains",
    "skill_aliases",
    "role_aliases",
    "skill_relationships",
    "candidate_entities",
    "candidate_skill_relationships",
    "skill_external_ids",
    "role_external_ids",
]

NEON_IMPORT_ORDER = LEGACY_TABLES + ["skill_embeddings"]

TABLE_PRIMARY_KEYS: dict[str, tuple[str, ...]] = {
    "domains": ("domain_id",),
    "knowledge_sources": ("source_id",),
    "skills": ("skill_id",),
    "roles": ("role_id",),
    "skill_domains": ("skill_id", "domain_id"),
    "role_domains": ("role_id", "domain_id"),
    "skill_aliases": ("alias_id",),
    "role_aliases": ("alias_id",),
    "skill_relationships": ("relationship_id",),
    "candidate_entities": ("candidate_entity_id",),
    "candidate_skill_relationships": ("candidate_relationship_id",),
    "skill_external_ids": ("external_id",),
    "role_external_ids": ("external_id",),
    "skill_embeddings": ("skill_id", "embedding_model"),
}

# Entity-type prefixes prevent collisions across tables that share legacy prefixes like AL-.
UUID_PK_ENTITY_BY_TABLE: dict[str, tuple[str, str]] = {
    "knowledge_sources": ("knowledge_source", "source_id"),
    "skill_aliases": ("skill_alias", "alias_id"),
    "role_aliases": ("role_alias", "alias_id"),
    "skill_relationships": ("skill_relationship", "relationship_id"),
    "candidate_entities": ("candidate_entity", "candidate_entity_id"),
    "candidate_skill_relationships": ("candidate_skill_relationship", "candidate_relationship_id"),
    "skill_external_ids": ("skill_external_id", "external_id"),
    "role_external_ids": ("role_external_id", "external_id"),
}

# Legacy source exports from ssks_db used external_id_id before v2 renamed the PK column to external_id.
LEGACY_PK_ALIAS_BY_TABLE: dict[str, str] = {
    "skill_external_ids": "external_id_id",
    "role_external_ids": "external_id_id",
}

UUID_FK_ENTITY_MAP: dict[str, list[tuple[str, str]]] = {
    "skill_aliases": [("source_id", "knowledge_source")],
    "role_aliases": [("source_id", "knowledge_source")],
    "skill_relationships": [("source_id", "knowledge_source")],
    "candidate_skill_relationships": [
        ("source_id", "knowledge_source"),
        ("canonical_relationship_id", "skill_relationship"),
    ],
    "skill_external_ids": [("source_id", "knowledge_source")],
    "role_external_ids": [("source_id", "knowledge_source")],
}

CANONICAL_ID_PATTERNS = {
    "domain_id": re.compile(r"^DOM-[A-Z0-9_]+$"),
    "skill_id": re.compile(r"^SK-\d+$"),
    "role_id": re.compile(r"^RL-\d+$"),
}


@dataclass(frozen=True)
class ColumnContract:
    name: str
    udt_name: str
    max_length: int | None
    nullable: bool


# Expected Neon v2 schema contract derived from infrastructure/neon/setup.sql.
EXPECTED_NEON_V2_SCHEMA: dict[str, list[ColumnContract]] = {
    "domains": [
        ColumnContract("domain_id", "varchar", 50, False),
        ColumnContract("name", "varchar", 255, False),
        ColumnContract("code", "varchar", 50, False),
        ColumnContract("description", "text", None, True),
        ColumnContract("status", "varchar", 50, False),
    ],
    "knowledge_sources": [
        ColumnContract("source_id", "uuid", None, False),
        ColumnContract("source_code", "varchar", 100, False),
        ColumnContract("source_name", "varchar", 255, False),
        ColumnContract("source_version", "varchar", 100, False),
        ColumnContract("last_synced_at", "timestamptz", None, True),
    ],
    "skills": [
        ColumnContract("skill_id", "varchar", 50, False),
        ColumnContract("preferred_name", "varchar", 255, False),
        ColumnContract("description", "text", None, True),
        ColumnContract("skill_type", "varchar", 100, False),
        ColumnContract("skill_nature", "varchar", 50, True),
        ColumnContract("status", "varchar", 50, False),
        ColumnContract("created_at", "timestamptz", None, False),
        ColumnContract("updated_at", "timestamptz", None, False),
    ],
    "roles": [
        ColumnContract("role_id", "varchar", 50, False),
        ColumnContract("preferred_name", "varchar", 255, False),
        ColumnContract("description", "text", None, True),
        ColumnContract("status", "varchar", 50, False),
        ColumnContract("created_at", "timestamptz", None, False),
        ColumnContract("updated_at", "timestamptz", None, False),
    ],
    "skill_domains": [
        ColumnContract("skill_id", "varchar", 50, False),
        ColumnContract("domain_id", "varchar", 50, False),
    ],
    "role_domains": [
        ColumnContract("role_id", "varchar", 50, False),
        ColumnContract("domain_id", "varchar", 50, False),
    ],
    "skill_aliases": [
        ColumnContract("alias_id", "uuid", None, False),
        ColumnContract("skill_id", "varchar", 50, False),
        ColumnContract("alias_text", "varchar", 255, False),
        ColumnContract("normalized_alias", "varchar", 255, False),
        ColumnContract("source_id", "uuid", None, True),
        ColumnContract("verification_status", "varchar", 50, False),
    ],
    "role_aliases": [
        ColumnContract("alias_id", "uuid", None, False),
        ColumnContract("role_id", "varchar", 50, False),
        ColumnContract("alias_text", "varchar", 255, False),
        ColumnContract("normalized_alias", "varchar", 255, False),
        ColumnContract("source_id", "uuid", None, True),
        ColumnContract("verification_status", "varchar", 50, False),
    ],
    "skill_relationships": [
        ColumnContract("relationship_id", "uuid", None, False),
        ColumnContract("source_skill_id", "varchar", 50, False),
        ColumnContract("target_skill_id", "varchar", 50, False),
        ColumnContract("relationship_type", "varchar", 50, False),
        ColumnContract("verification_status", "varchar", 50, False),
        ColumnContract("source_id", "uuid", None, True),
        ColumnContract("evidence_note", "text", None, True),
        ColumnContract("evidence_description", "text", None, True),
        ColumnContract("evidence_url", "varchar", 500, True),
        ColumnContract("reviewed_by", "uuid", None, True),
        ColumnContract("created_at", "timestamptz", None, False),
        ColumnContract("updated_at", "timestamptz", None, False),
    ],
    "candidate_entities": [
        ColumnContract("candidate_entity_id", "uuid", None, False),
        ColumnContract("entity_type", "varchar", 20, False),
        ColumnContract("submitted_name", "varchar", 255, False),
        ColumnContract("normalized_name", "varchar", 255, False),
        ColumnContract("description", "text", None, True),
        ColumnContract("proposed_skill_type", "varchar", 100, True),
        ColumnContract("proposed_skill_nature", "varchar", 50, True),
        ColumnContract("source_component", "varchar", 50, True),
        ColumnContract("source_reference", "varchar", 255, True),
        ColumnContract("review_status", "varchar", 50, False),
        ColumnContract("review_note", "text", None, True),
        ColumnContract("matched_entity_id", "varchar", 50, True),
        ColumnContract("created_at", "timestamptz", None, False),
        ColumnContract("reviewed_at", "timestamptz", None, True),
        ColumnContract("reviewed_by", "uuid", None, True),
    ],
    "candidate_skill_relationships": [
        ColumnContract("candidate_relationship_id", "uuid", None, False),
        ColumnContract("source_skill_id", "varchar", 50, False),
        ColumnContract("target_skill_id", "varchar", 50, False),
        ColumnContract("proposed_relationship_type", "varchar", 50, False),
        ColumnContract("confidence_score", "float8", None, True),
        ColumnContract("review_status", "varchar", 50, False),
        ColumnContract("source_id", "uuid", None, True),
        ColumnContract("review_note", "text", None, True),
        ColumnContract("evidence_description", "text", None, True),
        ColumnContract("evidence_url", "varchar", 500, True),
        ColumnContract("reviewed_by", "varchar", 100, True),
        ColumnContract("canonical_relationship_id", "uuid", None, True),
        ColumnContract("created_at", "timestamptz", None, False),
        ColumnContract("reviewed_at", "timestamptz", None, True),
    ],
    "skill_external_ids": [
        ColumnContract("external_id", "uuid", None, False),
        ColumnContract("skill_id", "varchar", 50, False),
        ColumnContract("source_id", "uuid", None, False),
        ColumnContract("external_identifier", "varchar", 255, False),
    ],
    "role_external_ids": [
        ColumnContract("external_id", "uuid", None, False),
        ColumnContract("role_id", "varchar", 50, False),
        ColumnContract("source_id", "uuid", None, False),
        ColumnContract("external_identifier", "varchar", 255, False),
    ],
    "skill_embeddings": [
        ColumnContract("skill_id", "varchar", 50, False),
        ColumnContract("embedding_model", "varchar", 150, False),
        ColumnContract("embedding_dimension", "int2", None, False),
        ColumnContract("embedding_text_hash", "bpchar", 64, False),
        ColumnContract("embedding", "vector", None, False),
        ColumnContract("generated_at", "timestamptz", None, False),
    ],
}


def legacy_id_to_uuid(entity_type: str, legacy_id: str) -> str:
    """Return a deterministic UUIDv5 string for a legacy identifier."""
    valid_types = {cfg[0] for cfg in UUID_PK_ENTITY_BY_TABLE.values()}
    if entity_type not in valid_types:
        raise ValueError(f"Unsupported entity_type for UUID conversion: {entity_type!r}")
    clean = (legacy_id or "").strip()
    if not clean:
        raise ValueError(f"Empty legacy_id for entity_type {entity_type!r}")
    return str(uuid.uuid5(SSKS_UUID_NAMESPACE, f"{entity_type}:{clean}"))


def load_env_file(path: Path) -> dict[str, str]:
    """Parse key=value pairs from an env file while stripping inline comments."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        val = val.strip()
        if "#" in val and not (val.startswith('"') or val.startswith("'")):
            val = val.split("#", 1)[0].strip()
        values[key.strip()] = val.strip('"').strip("'")
    return values


def _merged_env(env_file: Path | None = None) -> dict[str, str]:
    file_env = load_env_file(env_file or DEFAULT_INFRA_ENV)
    return {**file_env, **os.environ}


def normalize_asyncpg_dsn(dsn: str) -> str:
    """Convert SQLAlchemy asyncpg/psycopg URL prefixes into a plain postgresql DSN."""
    for prefix in ("postgresql+asyncpg://", "postgresql+psycopg://", "postgres://"):
        if dsn.startswith(prefix):
            return "postgresql://" + dsn[len(prefix):]
    return dsn


def redact_dsn(text: str) -> str:
    """Remove embedded credentials from URLs before logging or raising."""
    return re.sub(r"(postgres(?:ql)?(?:\+\w+)?://[^:/@\s]+):[^@\s]+@", r"\1:***@", str(text))


def get_source_dsn(env_file: Path | None = None) -> str:
    """Resolve local ssks_db DSN from environment or infrastructure/.env."""
    env = _merged_env(env_file)
    explicit = env.get("SSKS_SOURCE_DATABASE_URL") or env.get("SOURCE_DATABASE_URL")
    if explicit:
        return normalize_asyncpg_dsn(explicit)
    user = env.get("POSTGRES_USER", "skillbridge")
    password = env.get("POSTGRES_PASSWORD", "")
    port = env.get("POSTGRES_HOST_PORT", "15432")
    host = env.get("POSTGRES_HOST", "127.0.0.1")
    db_name = env.get("SSKS_SOURCE_DB", "ssks_db")
    if not password:
        raise RuntimeError("Missing POSTGRES_PASSWORD or SSKS_SOURCE_DATABASE_URL for local ssks_db")
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_neon_dsn(env_file: Path | None = None, *, use_owner: bool = False) -> str:
    """Resolve Neon skillaro DSN using ssks_svc credentials by default."""
    env = _merged_env(env_file)
    if use_owner:
        owner_url = env.get("NEON_OWNER_URL")
        if not owner_url:
            raise RuntimeError("NEON_OWNER_URL is not configured in environment or infrastructure/.env")
        return normalize_asyncpg_dsn(owner_url)

    explicit = env.get("NEON_SSKS_DATABASE_URL")
    if explicit:
        return normalize_asyncpg_dsn(explicit)

    host = env.get("NEON_HOST")
    password = env.get("NEON_SSKS_PASSWORD")
    db_name = env.get("NEON_DB", "skillaro")
    if not host or not password:
        raise RuntimeError(
            "Neon SSKS credentials not configured. Set NEON_HOST and NEON_SSKS_PASSWORD in infrastructure/.env."
        )
    return f"postgresql://ssks_svc:{password}@{host}/{db_name}?sslmode=require"


def guard_output_dir(output_dir: Path) -> Path:
    """Prevent accidental writes into seed/import_ready or root seed/ssks_neon_import."""
    resolved = output_dir.resolve()
    if resolved == PROTECTED_IMPORT_READY_DIR or PROTECTED_IMPORT_READY_DIR in resolved.parents:
        raise PermissionError(f"Refusing to write inside protected directory: {resolved}")
    if resolved == LEGACY_NEON_SEED_DIR:
        raise PermissionError(
            f"Refusing to write directly into {resolved}; use a subdirectory such as exports/current_ssks_db."
        )
    return resolved


def encode_csv_value(value: Any) -> str:
    """Encode Python/DB values to UTF-8 CSV text while preserving NULL via \\N."""
    if value is None:
        return NULL_MARKER
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    if text == NULL_MARKER:
        raise ValueError("Source value collides with CSV NULL marker '\\N'")
    return text


def decode_csv_value(raw: str | None) -> str | None:
    """Decode CSV field back to None when the NULL marker is encountered."""
    if raw is None or raw == NULL_MARKER:
        return None
    return raw


def write_csv_rows(path: Path, columns: list[str], rows: list[dict[str, Any]], *, overwrite: bool = False) -> str:
    """Write rows as UTF-8 CSV with headers and return the file SHA-256 hex digest."""
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file without --overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([encode_csv_value(row.get(col)) for col in columns])
    return file_sha256(path)


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str | None]]]:
    """Read a UTF-8 CSV exported with NULL_MARKER into headers and decoded row dicts."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = [{k: decode_csv_value(v) for k, v in raw.items()} for raw in reader]
    return headers, rows


def file_sha256(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def construct_embedding_text(preferred_name: str, description: str | None) -> str:
    """Format canonical skill text identically to the C03 embedding specification."""
    clean_name = (preferred_name or "").strip()
    clean_desc = (description or "").strip()
    if clean_desc:
        return f"{clean_name}. {clean_desc}"
    return clean_name


def compute_text_hash(text: str) -> str:
    """Return SHA-256 hex digest of embedding input text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
