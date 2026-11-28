import os
import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy import String, cast, select
from sqlalchemy.dialects import postgresql

import app.models  # noqa: F401
from app.db.base import Base
from app.models.embeddings import SkillEmbedding
from app.models.relationships import SkillRelationship
from scripts.migration.common import EXPECTED_NEON_V2_SCHEMA, TABLE_PRIMARY_KEYS


def test_orm_models_match_neon_v2_schema_contract():
    """Verify every SQLAlchemy table, column, nullability, and PK matches setup.sql."""
    assert set(EXPECTED_NEON_V2_SCHEMA.keys()) == set(Base.metadata.tables.keys())

    for table_name, expected_cols in EXPECTED_NEON_V2_SCHEMA.items():
        table = Base.metadata.tables[table_name]
        actual_cols = {col.name: col for col in table.columns}
        expected_names = [c.name for c in expected_cols]
        assert list(actual_cols.keys()) == expected_names, f"Column mismatch on {table_name}"

        for spec in expected_cols:
            col = actual_cols[spec.name]
            assert col.nullable == spec.nullable, f"Nullability mismatch on {table_name}.{spec.name}"
            if spec.udt_name == "uuid":
                assert isinstance(col.type, sa.Uuid), f"Expected UUID column for {table_name}.{spec.name}"

        actual_pk = tuple(col.name for col in table.primary_key.columns)
        assert actual_pk == TABLE_PRIMARY_KEYS[table_name], f"PK mismatch on {table_name}"


def test_postgresql_dialect_sql_compilation_for_vectors_and_uuid_search():
    """Verify pgvector CAST and UUID text CAST compile cleanly for PostgreSQL."""
    vec_stmt = sa.insert(SkillEmbedding).values(
        skill_id="SK-000001",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        embedding_dimension=384,
        embedding_text_hash="a" * 64,
        embedding=[0.1] * 384,
    )
    compiled_vec = str(vec_stmt.compile(dialect=postgresql.dialect()))
    assert "CAST(%(embedding)s AS vector(384))" in compiled_vec

    search_stmt = select(SkillRelationship).where(
        cast(SkillRelationship.relationship_id, String).ilike("%abc%")
    )
    compiled_search = str(search_stmt.compile(dialect=postgresql.dialect()))
    assert "CAST(skill_relationships.relationship_id AS VARCHAR)" in compiled_search


@pytest.mark.anyio
async def test_postgres_live_readonly_compatibility_if_configured():
    """When SSKS_PG_TEST_URL is provided, verify ORM queries execute cleanly against PostgreSQL."""
    pg_url = os.environ.get("SSKS_PG_TEST_URL")
    if not pg_url:
        pytest.skip("SSKS_PG_TEST_URL not set; skipping live PostgreSQL test")

    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    schema = os.environ.get("DB_SCHEMA", "ssks")
    engine = create_async_engine(
        pg_url,
        connect_args={"server_settings": {"search_path": f"{schema}, public"}},
    )
    try:
        async with AsyncSession(engine) as session:
            skills_count = (await session.execute(sa.text("SELECT count(*) FROM skills"))).scalar_one()
            emb_row = (await session.scalars(select(SkillEmbedding).limit(1))).first()
            rel_rows = (
                await session.scalars(
                    select(SkillRelationship)
                    .where(cast(SkillRelationship.relationship_id, String).ilike("%-%"))
                    .limit(5)
                )
            ).all()
            assert skills_count > 0
            assert emb_row is not None
            assert len(emb_row.embedding) == 384
            for rel in rel_rows:
                assert isinstance(rel.relationship_id, uuid.UUID)
    finally:
        await engine.dispose()
