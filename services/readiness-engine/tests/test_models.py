import pytest

import app.models  # noqa: F401
from app.db.base import Base


def test_all_sixteen_models_registered():
    expected_tables = {
        "knowledge_snapshots",
        "cached_skills",
        "cached_aliases",
        "cached_relationships",
        "cached_skill_embeddings",
        "user_skill_profiles",
        "user_skill_profile_skills",
        "skill_evidence",
        "industry_profiles",
        "industry_profile_requirements",
        "industry_skill_evidence",
        "analyses",
        "analysis_skill_results",
        "analysis_priority_skills",
        "analysis_reports",
        "candidate_discovery_runs",
    }
    registered_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(registered_tables)
    assert len(registered_tables) == 16


def test_user_skill_profile_schema_fields():
    tables = Base.metadata.tables

    # 1. user_skill_profiles table and user_id column
    usp_table = tables["user_skill_profiles"]
    assert "user_id" in usp_table.columns
    assert "profile_version" in usp_table.columns
    assert "student_id" not in usp_table.columns
    # Uniqueness constraint on (user_id, profile_version)
    uq_names = [uc.name for uc in usp_table.constraints if uc.__class__.__name__ == "UniqueConstraint"]
    assert "uq_user_skill_profile_version" in uq_names

    # 2. user_skill_profile_skills table and foreign key
    usps_table = tables["user_skill_profile_skills"]
    assert "user_skill_profile_id" in usps_table.columns
    assert "student_profile_id" not in usps_table.columns
    assert any(
        fk.target_fullname == "user_skill_profiles.id"
        for fk in usps_table.foreign_keys
    )

    # 3. skill_evidence foreign key
    se_table = tables["skill_evidence"]
    assert "user_skill_profile_skill_id" in se_table.columns
    assert "student_profile_skill_id" not in se_table.columns
    assert any(
        fk.target_fullname == "user_skill_profile_skills.id"
        for fk in se_table.foreign_keys
    )

    # 4. analyses foreign key and user_id retention
    analyses_table = tables["analyses"]
    assert "user_id" in analyses_table.columns
    assert "user_skill_profile_id" in analyses_table.columns
    assert "student_profile_id" not in analyses_table.columns
    assert any(
        fk.target_fullname == "user_skill_profiles.id"
        for fk in analyses_table.foreign_keys
    )

    # 5. analysis_skill_results column renames
    asr_table = tables["analysis_skill_results"]
    assert "user_skill_profile_skill_id" in asr_table.columns
    assert "student_profile_skill_id" not in asr_table.columns
    assert "user_proficiency" in asr_table.columns
    assert "student_proficiency" not in asr_table.columns

    # 6. analysis_priority_skills column renames
    aps_table = tables["analysis_priority_skills"]
    assert "user_proficiency" in aps_table.columns
    assert "student_proficiency" not in aps_table.columns


def test_snapshot_child_foreign_keys():
    snapshot_table = Base.metadata.tables["knowledge_snapshots"]
    assert "snapshot_id" in snapshot_table.primary_key.columns

    child_tables = [
        "cached_skills",
        "cached_aliases",
        "cached_relationships",
        "cached_skill_embeddings",
    ]
    for table_name in child_tables:
        table = Base.metadata.tables[table_name]
        fk_targets = [
            (fk.parent.name, fk.target_fullname)
            for fk in table.foreign_keys
            if "knowledge_snapshots" in fk.target_fullname
        ]
        assert any(
            parent == "snapshot_id" and target == "knowledge_snapshots.snapshot_id"
            for parent, target in fk_targets
        ), f"{table_name} missing foreign key to knowledge_snapshots.snapshot_id"


def test_composite_primary_keys():
    tables = Base.metadata.tables

    assert [c.name for c in tables["cached_skills"].primary_key.columns] == [
        "snapshot_id",
        "skill_id",
    ]
    assert [c.name for c in tables["cached_aliases"].primary_key.columns] == [
        "snapshot_id",
        "alias_id",
    ]
    assert [c.name for c in tables["cached_relationships"].primary_key.columns] == [
        "snapshot_id",
        "relationship_id",
    ]
    assert [c.name for c in tables["cached_skill_embeddings"].primary_key.columns] == [
        "snapshot_id",
        "skill_id",
        "embedding_model",
    ]


def test_embedding_column_pgvector():
    embedding_col = Base.metadata.tables["cached_skill_embeddings"].columns["embedding"]
    assert embedding_col.type.__class__.__name__ in ("Vector", "VECTOR")


@pytest.mark.anyio
async def test_create_tables_initialization(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock

    from app.db.session import create_tables

    mock_conn = AsyncMock()
    mock_conn.dialect.name = "postgresql"
    mock_begin = MagicMock()
    mock_begin.__aenter__.return_value = mock_conn

    mock_engine = MagicMock()
    mock_engine.begin.return_value = mock_begin

    monkeypatch.setattr("app.db.session.get_engine", lambda: mock_engine)

    await create_tables()

    # Confirms extensions and metadata.create_all were executed
    assert mock_conn.execute.await_count == 2
    assert mock_conn.run_sync.await_count == 1
    args, _ = mock_conn.run_sync.call_args
    assert args[0] == Base.metadata.create_all
