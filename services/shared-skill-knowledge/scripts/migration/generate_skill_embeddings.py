"""Regenerate 384-dim SBERT skill embeddings into Neon ssks.skill_embeddings."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import logging
import math
import sys
from pathlib import Path
from typing import Any

import asyncpg

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.migration.common import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_REVISION,
    EMBEDDING_TEXT_METHOD,
    EXPECTED_EMBEDDING_DIMENSION,
    compute_text_hash,
    construct_embedding_text,
    get_neon_dsn,
    redact_dsn,
)

logger = logging.getLogger("ssks.migration.embeddings")


def validate_vector(vector: Any, expected_dim: int = EXPECTED_EMBEDDING_DIMENSION) -> list[float]:
    """Ensure embedding vector has exact expected dimension and only finite floats."""
    if vector is None:
        raise ValueError("Vector cannot be None")
    if hasattr(vector, "tolist"):
        vec_list = [float(x) for x in vector.tolist()]
    elif isinstance(vector, (list, tuple)):
        vec_list = [float(x) for x in vector]
    else:
        raise TypeError(f"Unsupported vector type: {type(vector)}")

    if len(vec_list) != expected_dim:
        raise ValueError(f"Expected {expected_dim} dimensions, got {len(vec_list)}")
    for idx, val in enumerate(vec_list):
        if not math.isfinite(val):
            raise ValueError(f"Non-finite value at index {idx}: {val}")
    return vec_list


async def generate_embeddings_into_neon(
    *,
    env_file: Path | None = None,
    schema: str = "ssks",
    model_id: str = DEFAULT_EMBEDDING_MODEL,
    model_revision: str = DEFAULT_EMBEDDING_REVISION,
    local_only: bool = False,
    batch_size: int = 64,
    force: bool = False,
    apply: bool = False,
    confirm_database: str | None = None,
) -> dict[str, Any]:
    """Generate and optionally persist 384-dim embeddings for all skills in Neon."""
    dsn = get_neon_dsn(env_file)
    try:
        conn = await asyncpg.connect(dsn, timeout=12)
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to Neon: {redact_dsn(exc)}") from None

    summary: dict[str, Any] = {
        "database": None,
        "schema": schema,
        "model_id": model_id,
        "model_revision": model_revision,
        "expected_dimension": EXPECTED_EMBEDDING_DIMENSION,
        "normalize_embeddings": True,
        "text_generation_method": EMBEDDING_TEXT_METHOD,
        "total_skills": 0,
        "already_valid": 0,
        "to_generate": 0,
        "inserted_or_updated": 0,
        "applied": False,
    }

    try:
        db_name = await conn.fetchval("SELECT current_database()")
        summary["database"] = db_name
        if apply and confirm_database != db_name:
            raise RuntimeError(f"--confirm-database must equal connected database ({db_name!r})")

        skills = await conn.fetch(
            f'SELECT skill_id, preferred_name, description FROM "{schema}"."skills" ORDER BY skill_id ASC'
        )
        summary["total_skills"] = len(skills)
        if not skills:
            raise RuntimeError(f"No skills found in {schema}.skills; import skills before generating embeddings.")

        existing_rows = await conn.fetch(
            f"""
            SELECT skill_id, embedding_text_hash, embedding_dimension
            FROM "{schema}"."skill_embeddings"
            WHERE embedding_model = $1
            """,
            model_id,
        )
        existing_map = {
            r["skill_id"]: (r["embedding_text_hash"], r["embedding_dimension"]) for r in existing_rows
        }

        work: list[tuple[str, str, str]] = []
        for s in skills:
            text = construct_embedding_text(s["preferred_name"], s["description"])
            text_hash = compute_text_hash(text)
            if not force and s["skill_id"] in existing_map:
                ex_hash, ex_dim = existing_map[s["skill_id"]]
                if ex_hash == text_hash and ex_dim == EXPECTED_EMBEDDING_DIMENSION:
                    summary["already_valid"] += 1
                    continue
            work.append((s["skill_id"], text, text_hash))

        summary["to_generate"] = len(work)
        logger.info(
            "Skills=%d, already_valid=%d, to_generate=%d",
            summary["total_skills"],
            summary["already_valid"],
            summary["to_generate"],
        )

        if not apply or not work:
            return summary

        try:
            st_module = importlib.import_module("sentence_transformers")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Missing 'sentence-transformers' in the active Python environment. "
                "Run this script with an environment that has it installed (for example global 'python' "
                "instead of the lightweight service .venv), or install 'sentence-transformers'."
            ) from exc

        logger.info("Loading embedding model %s (revision=%s)", model_id, model_revision)
        try:
            model = st_module.SentenceTransformer(model_id, revision=model_revision, local_files_only=True)
        except Exception:
            if local_only:
                raise
            logger.info("Local cache miss for %s@%s; fetching from HuggingFace Hub", model_id, model_revision)
            model = st_module.SentenceTransformer(model_id, revision=model_revision, local_files_only=False)
        actual_dim = model.get_sentence_embedding_dimension()
        if actual_dim != EXPECTED_EMBEDDING_DIMENSION:
            raise RuntimeError(
                f"Model {model_id!r} outputs {actual_dim} dimensions, expected {EXPECTED_EMBEDDING_DIMENSION}"
            )

        upsert_sql = f"""
        INSERT INTO "{schema}"."skill_embeddings"
            (skill_id, embedding_model, embedding_dimension, embedding_text_hash, embedding, generated_at)
        VALUES ($1, $2, $3, $4, $5::vector, now())
        ON CONFLICT (skill_id, embedding_model) DO UPDATE SET
            embedding_dimension = EXCLUDED.embedding_dimension,
            embedding_text_hash = EXCLUDED.embedding_text_hash,
            embedding = EXCLUDED.embedding,
            generated_at = now()
        """

        total_batches = (len(work) + batch_size - 1) // batch_size
        for batch_idx in range(total_batches):
            batch = work[batch_idx * batch_size : (batch_idx + 1) * batch_size]
            texts = [item[1] for item in batch]
            vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            records = []
            for (skill_id, _, text_hash), vec in zip(batch, vectors):
                clean = validate_vector(vec, EXPECTED_EMBEDDING_DIMENSION)
                vec_literal = "[" + ",".join(repr(v) for v in clean) + "]"
                records.append((skill_id, model_id, EXPECTED_EMBEDDING_DIMENSION, text_hash, vec_literal))

            async with conn.transaction():
                await conn.executemany(upsert_sql, records)
            summary["inserted_or_updated"] += len(records)
            logger.info("Committed embedding batch %d/%d (%d rows)", batch_idx + 1, total_batches, len(records))

        summary["applied"] = True
        return summary
    finally:
        await conn.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--schema", default="ssks")
    parser.add_argument("--model-id", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--model-revision", default=DEFAULT_EMBEDDING_REVISION)
    parser.add_argument("--local-only", action="store_true", help="Fail instead of downloading if pinned model is not cached.")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--force", action="store_true", help="Regenerate embeddings even when text hashes match.")
    parser.add_argument("--dry-run", action="store_true", help="Report work without writing (default).")
    parser.add_argument("--apply", action="store_true", help="Generate and write embeddings to Neon.")
    parser.add_argument("--confirm-database", help="Must equal Neon database name when using --apply.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    try:
        summary = asyncio.run(
            generate_embeddings_into_neon(
                env_file=args.env_file,
                schema=args.schema,
                model_id=args.model_id,
                model_revision=args.model_revision,
                local_only=args.local_only,
                batch_size=args.batch_size,
                force=args.force,
                apply=args.apply,
                confirm_database=args.confirm_database,
            )
        )
    except Exception as exc:
        logger.error("Embedding generation failed: %s", redact_dsn(exc))
        return 2

    print("Skill Embeddings Summary:")
    for key, val in summary.items():
        print(f"  {key:22}: {val}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
