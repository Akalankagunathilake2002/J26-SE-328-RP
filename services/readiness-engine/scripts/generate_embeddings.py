import argparse
import asyncio
import hashlib
import logging
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Add service root to path for direct script execution
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config.settings import get_settings
from app.models.cache import CachedSkill, CachedSkillEmbedding, KnowledgeSnapshot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("generate_embeddings")

DEFAULT_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 64


# Deterministically format skill text from preferred name and optional description
def construct_embedding_text(preferred_name: str, description: str | None) -> str:
    clean_name = (preferred_name or "").strip()
    clean_desc = (description or "").strip()
    if clean_desc:
        return f"{clean_name}. {clean_desc}"
    return clean_name


# Compute SHA-256 digest of input text to detect stale embeddings when descriptions change
def compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Ensure vector length matches model dimensions and contains only finite float numbers
def validate_vector(vector: Any, expected_dim: int) -> list[float]:
    if vector is None:
        raise ValueError("Vector cannot be None")

    if isinstance(vector, np.ndarray):
        vec_list = vector.tolist()
    elif isinstance(vector, (list, tuple)):
        vec_list = [float(x) for x in vector]
    else:
        raise TypeError(f"Unsupported vector container type: {type(vector)}")

    if len(vec_list) != expected_dim:
        raise ValueError(
            f"Vector dimension mismatch: expected {expected_dim}, got {len(vec_list)}"
        )

    for i, val in enumerate(vec_list):
        if not math.isfinite(val):
            raise ValueError(f"Non-finite value at index {i}: {val}")

    return vec_list


# Generate and persist static SBERT embeddings for active snapshot canonical skills
async def generate_skill_embeddings(
    database_url: str,
    model_id: str = DEFAULT_MODEL_ID,
    batch_size: int = DEFAULT_BATCH_SIZE,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    from sentence_transformers import SentenceTransformer

    logger.info("Loading SBERT embedding model: %s", model_id)
    model = SentenceTransformer(model_id)

    # Determine embedding dimension from model configuration
    if hasattr(model, "get_embedding_dimension"):
        expected_dim = model.get_embedding_dimension()
    else:
        expected_dim = model.get_sentence_embedding_dimension()

    if expected_dim is None:
        dummy = model.encode("test", normalize_embeddings=True)
        expected_dim = int(dummy.shape[0])

    logger.info("Model output vector dimension: %d", expected_dim)

    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    summary = {
        "snapshot_id": None,
        "snapshot_version": None,
        "model_id": model_id,
        "embedding_dimension": expected_dim,
        "total_canonical_skills": 0,
        "already_valid_skipped": 0,
        "to_process": 0,
        "inserted_or_updated": 0,
        "failed_skill_ids": [],
    }

    try:
        async with session_factory() as session:
            # Locate active knowledge snapshot or fallback to most recent snapshot
            snap_stmt = (
                select(KnowledgeSnapshot)
                .where(KnowledgeSnapshot.is_active.is_(True))
                .order_by(KnowledgeSnapshot.imported_at.desc())
                .limit(1)
            )
            snapshot = (await session.execute(snap_stmt)).scalar_one_or_none()

            if not snapshot:
                fallback_stmt = (
                    select(KnowledgeSnapshot)
                    .order_by(KnowledgeSnapshot.imported_at.desc())
                    .limit(1)
                )
                snapshot = (await session.execute(fallback_stmt)).scalar_one_or_none()

            if not snapshot:
                raise RuntimeError(
                    "No knowledge snapshot found in database. Import a snapshot first."
                )

            summary["snapshot_id"] = str(snapshot.snapshot_id)
            summary["snapshot_version"] = snapshot.version

            # Load canonical skills for active snapshot
            skills_stmt = (
                select(CachedSkill)
                .where(CachedSkill.snapshot_id == snapshot.snapshot_id)
                .order_by(CachedSkill.skill_id.asc())
            )
            skills = (await session.execute(skills_stmt)).scalars().all()
            summary["total_canonical_skills"] = len(skills)

            # Query existing embeddings to support idempotent recovery
            existing_stmt = select(
                CachedSkillEmbedding.skill_id,
                CachedSkillEmbedding.embedding_text_hash,
                CachedSkillEmbedding.embedding_dimension,
            ).where(
                CachedSkillEmbedding.snapshot_id == snapshot.snapshot_id,
                CachedSkillEmbedding.embedding_model == model_id,
            )
            existing_rows = (await session.execute(existing_stmt)).all()
            existing_map = {
                row.skill_id: (row.embedding_text_hash, row.embedding_dimension)
                for row in existing_rows
            }

            # Filter skills that already have matching embeddings
            skills_to_embed: list[tuple[CachedSkill, str, str]] = []
            for skill in skills:
                text = construct_embedding_text(skill.preferred_name, skill.description)
                text_hash = compute_text_hash(text)

                if not force and skill.skill_id in existing_map:
                    ex_hash, ex_dim = existing_map[skill.skill_id]
                    if ex_hash == text_hash and ex_dim == expected_dim:
                        summary["already_valid_skipped"] += 1
                        continue

                skills_to_embed.append((skill, text, text_hash))

            summary["to_process"] = len(skills_to_embed)
            logger.info(
                "Skipping %d valid embeddings. Generating %d embeddings...",
                summary["already_valid_skipped"],
                summary["to_process"],
            )

            if dry_run:
                logger.info("Dry-run complete. No database writes performed.")
                return summary

            # Process in transactional batches to maintain recovery checkpoints
            total_batches = (
                (len(skills_to_embed) + batch_size - 1) // batch_size
                if skills_to_embed
                else 0
            )

            for batch_idx in range(total_batches):
                start = batch_idx * batch_size
                batch = skills_to_embed[start : start + batch_size]
                texts = [item[1] for item in batch]

                try:
                    # Unit-normalized embeddings allow cosine distance via dot product
                    raw_vectors = model.encode(
                        texts,
                        normalize_embeddings=True,
                        show_progress_bar=False,
                    )

                    for (skill, text, text_hash), vec in zip(batch, raw_vectors):
                        try:
                            clean_vec = validate_vector(vec, expected_dim)
                        except (ValueError, TypeError) as val_err:
                            logger.error(
                                "Validation failure for skill %s: %s",
                                skill.skill_id,
                                val_err,
                            )
                            summary["failed_skill_ids"].append(skill.skill_id)
                            continue

                        # Upsert embedding row idempotently
                        stmt = (
                            pg_insert(CachedSkillEmbedding)
                            .values(
                                snapshot_id=snapshot.snapshot_id,
                                skill_id=skill.skill_id,
                                embedding_model=model_id,
                                embedding_dimension=expected_dim,
                                embedding_text_hash=text_hash,
                                embedding_text=text,
                                embedding=clean_vec,
                            )
                            .on_conflict_do_update(
                                index_elements=[
                                    "snapshot_id",
                                    "skill_id",
                                    "embedding_model",
                                ],
                                set_={
                                    "embedding_dimension": expected_dim,
                                    "embedding_text_hash": text_hash,
                                    "embedding_text": text,
                                    "embedding": clean_vec,
                                    "generated_at": func.now(),
                                },
                            )
                        )
                        await session.execute(stmt)
                        summary["inserted_or_updated"] += 1

                    await session.commit()
                    logger.info(
                        "Committed batch %d/%d (%d skills)",
                        batch_idx + 1,
                        total_batches,
                        len(batch),
                    )
                except (SQLAlchemyError, RuntimeError) as batch_err:
                    await session.rollback()
                    logger.error("Error on batch %d: %s", batch_idx + 1, batch_err)
                    for item in batch:
                        summary["failed_skill_ids"].append(item[0].skill_id)

    finally:
        await engine.dispose()

    return summary


def main() -> None:
    settings = get_settings()
    default_db_url = settings.database_url
    if "localhost:5432" in default_db_url:
        default_db_url = default_db_url.replace(":5432", ":15432")

    parser = argparse.ArgumentParser(
        description="Generate and persist static SBERT embeddings for Skillaro C03 canonical skills."
    )
    parser.add_argument(
        "--database-url",
        default=default_db_url,
        help="Database connection URL",
    )
    parser.add_argument(
        "--model-id",
        default=DEFAULT_MODEL_ID,
        help=f"SBERT model identifier (default: {DEFAULT_MODEL_ID})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Batch size (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate existing embeddings even if text hashes match",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate embedding generation without writing to database",
    )

    args = parser.parse_args()

    result = asyncio.run(
        generate_skill_embeddings(
            database_url=args.database_url,
            model_id=args.model_id,
            batch_size=args.batch_size,
            force=args.force,
            dry_run=args.dry_run,
        )
    )

    print("\n--- Embedding Generation Summary ---")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
