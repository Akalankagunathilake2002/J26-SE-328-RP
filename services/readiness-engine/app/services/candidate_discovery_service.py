import asyncio
import logging
import math
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.settings import get_settings
from app.db.session import get_sessionmaker
from app.models.analysis import CandidateDiscoveryRun
from app.models.cache import CachedSkillEmbedding

logger = logging.getLogger(__name__)


# Compute cosine similarity safely between two vectors, returning None for invalid inputs
def compute_cosine_similarity(
    vec_a: Sequence[float] | None,
    vec_b: Sequence[float] | None,
    expected_dim: int | None = None,
) -> float | None:
    if vec_a is None or vec_b is None:
        return None
    if len(vec_a) == 0 or len(vec_b) == 0:
        return None
    if len(vec_a) != len(vec_b):
        return None
    if expected_dim is not None and len(vec_a) != expected_dim:
        return None

    dot_product = 0.0
    norm_a_sq = 0.0
    norm_b_sq = 0.0

    for a, b in zip(vec_a, vec_b):
        if not math.isfinite(a) or not math.isfinite(b):
            return None
        dot_product += a * b
        norm_a_sq += a * a
        norm_b_sq += b * b

    # Return zero similarity safely if either vector has zero magnitude
    if norm_a_sq <= 0.0 or norm_b_sq <= 0.0:
        return 0.0

    similarity = dot_product / (math.sqrt(norm_a_sq) * math.sqrt(norm_b_sq))
    return max(-1.0, min(1.0, similarity))


@dataclass(frozen=True)
class CandidatePair:
    source_skill_id: str
    target_skill_id: str
    similarity_score: float


# Filter candidate pairs meeting threshold and rank deterministically with stable tie-breaking
def filter_and_rank_candidates(
    candidate_pairs: Sequence[CandidatePair],
    threshold: float,
    max_candidates: int,
) -> list[CandidatePair]:
    eligible = [cp for cp in candidate_pairs if cp.similarity_score >= threshold]

    # Sort descending by similarity score, breaking ties alphabetically by skill IDs
    eligible.sort(
        key=lambda c: (-c.similarity_score, c.source_skill_id, c.target_skill_id)
    )

    if max_candidates > 0:
        return eligible[:max_candidates]
    return eligible


# Generate eligible skill pairs by excluding identical skills and verified taxonomy relationships
def generate_candidate_skill_pairs(
    student_skill_ids: Sequence[str] | None = None,
    requirement_skill_ids: Sequence[str] | None = None,
    verified_relationship_pairs: set[tuple[str, str]] | None = None,
    unmatched_student_skill_ids: Sequence[str] | None = None,
    unmatched_requirement_skill_ids: Sequence[str] | None = None,
) -> list[tuple[str, str]]:
    stu_ids = (
        student_skill_ids
        if student_skill_ids is not None
        else (unmatched_student_skill_ids or [])
    )
    req_ids = (
        requirement_skill_ids
        if requirement_skill_ids is not None
        else (unmatched_requirement_skill_ids or [])
    )
    verified_pairs = verified_relationship_pairs or set()

    unique_pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for stu_id in stu_ids:
        clean_stu = stu_id.strip() if stu_id else ""
        if not clean_stu:
            continue
        for req_id in req_ids:
            clean_req = req_id.strip() if req_id else ""
            if not clean_req:
                continue
            if clean_stu == clean_req:
                continue

            pair = (clean_stu, clean_req)
            reverse_pair = (clean_req, clean_stu)

            # Exclude pairs already connected by a verified relationship in either direction
            if (
                pair in verified_pairs
                or reverse_pair in verified_pairs
            ):
                continue

            if pair not in seen:
                seen.add(pair)
                unique_pairs.append(pair)

    return unique_pairs


# Submit proposed candidate relationship to SSKS with bounded retries for transient failures
async def submit_candidate_to_ssks(
    client: httpx.AsyncClient,
    ssks_base_url: str,
    source_skill_id: str,
    target_skill_id: str,
    similarity_score: float,
    analysis_id: uuid.UUID,
    max_retries: int = 3,
) -> tuple[bool, str]:
    endpoint = f"{ssks_base_url.rstrip('/')}/ssks/candidates/relationships"

    # In SSKS, source_id references knowledge_sources; source C03 is recorded in review_note
    payload = {
        "source_skill_id": source_skill_id,
        "target_skill_id": target_skill_id,
        "proposed_relationship_type": "RELATED_TO",
        "confidence_score": round(similarity_score, 4),
        "source_id": None,
        "review_note": (
            f"Discovered by C03 Readiness Engine (Analysis: {analysis_id}) "
            f"with cosine similarity {similarity_score:.4f}"
        ),
    }

    for attempt in range(max_retries):
        try:
            response = await client.post(endpoint, json=payload)
            if response.status_code == 201:
                return True, "CREATED"
            elif response.status_code == 409:
                # Candidate or canonical relationship already exists in SSKS
                logger.info(
                    "Candidate pair (%s, %s) already registered in SSKS (409 Conflict)",
                    source_skill_id,
                    target_skill_id,
                )
                return True, "ALREADY_EXISTS"
            elif 400 <= response.status_code < 500:
                logger.warning(
                    "SSKS rejected candidate submission with status %d: %s",
                    response.status_code,
                    response.text,
                )
                return False, f"HTTP_{response.status_code}"
            else:
                logger.warning(
                    "SSKS server error %d on attempt %d: %s",
                    response.status_code,
                    attempt + 1,
                    response.text,
                )
        except (httpx.TimeoutException, httpx.NetworkError) as net_err:
            logger.warning(
                "SSKS network exception on attempt %d/%d: %s",
                attempt + 1,
                max_retries,
                net_err,
            )

        if attempt < max_retries - 1:
            await asyncio.sleep(0.5 * (2**attempt))

    return False, "MAX_RETRIES_EXCEEDED"


class CandidateDiscoveryService:
    # Orchestrate candidate discovery, embedding similarity evaluation, and SSKS submission
    async def run_candidate_discovery(
        self,
        analysis_id: uuid.UUID,
        snapshot_id: uuid.UUID,
        requirement_skill_ids: list[str] | None = None,
        student_skill_ids: list[str] | None = None,
        verified_relationship_pairs: set[tuple[str, str]] | None = None,
        threshold: float | None = None,
        max_candidates: int | None = None,
        embedding_model: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        unmatched_requirement_skill_ids: list[str] | None = None,
        unmatched_student_skill_ids: list[str] | None = None,
    ) -> CandidateDiscoveryRun | None:
        settings = get_settings()
        effective_threshold = (
            threshold
            if threshold is not None
            else settings.candidate_similarity_threshold
        )
        effective_max = (
            max_candidates
            if max_candidates is not None
            else settings.candidate_max_submissions_per_run
        )
        model_id = embedding_model or settings.candidate_discovery_embedding_model

        effective_req_ids = (
            requirement_skill_ids
            if requirement_skill_ids is not None
            else (unmatched_requirement_skill_ids or [])
        )
        effective_stu_ids = (
            student_skill_ids
            if student_skill_ids is not None
            else (unmatched_student_skill_ids or [])
        )
        verified_pairs = verified_relationship_pairs or set()

        factory = session_factory or get_sessionmaker()
        run_id = uuid.uuid4()
        started_at = datetime.now(UTC)

        async with factory() as session:
            # Initialize tracking record in RUNNING status
            discovery_run = CandidateDiscoveryRun(
                id=run_id,
                analysis_id=analysis_id,
                embedding_model=model_id,
                similarity_threshold=effective_threshold,
                status="RUNNING",
                candidates_submitted_count=0,
                started_at=started_at,
            )
            session.add(discovery_run)
            await session.commit()

            try:
                candidate_skill_pairs = generate_candidate_skill_pairs(
                    student_skill_ids=effective_stu_ids,
                    requirement_skill_ids=effective_req_ids,
                    verified_relationship_pairs=verified_pairs,
                )

                if not candidate_skill_pairs:
                    discovery_run.status = "COMPLETED"
                    discovery_run.completed_at = datetime.now(UTC)
                    discovery_run.candidates_submitted_count = 0
                    await session.commit()
                    return discovery_run

                # Load existing cached embeddings for all candidate skills in the snapshot
                all_needed_skills = list(
                    {s for pair in candidate_skill_pairs for s in pair}
                )
                stmt = select(CachedSkillEmbedding).where(
                    CachedSkillEmbedding.snapshot_id == snapshot_id,
                    CachedSkillEmbedding.embedding_model == model_id,
                    CachedSkillEmbedding.skill_id.in_(all_needed_skills),
                )
                res = await session.execute(stmt)
                db_embeddings = res.scalars().all()

                embedding_map: dict[str, tuple[list[float], int]] = {}
                for row in db_embeddings:
                    if row.embedding is not None:
                        embedding_map[row.skill_id] = (
                            row.embedding,
                            row.embedding_dimension,
                        )

                # Compute cosine similarities for pairs with valid cached embeddings
                scored_pairs: list[CandidatePair] = []
                for stu_id, req_id in candidate_skill_pairs:
                    stu_emb_info = embedding_map.get(stu_id)
                    req_emb_info = embedding_map.get(req_id)

                    if not stu_emb_info or not req_emb_info:
                        continue

                    stu_vec, stu_dim = stu_emb_info
                    req_vec, req_dim = req_emb_info

                    if stu_dim != req_dim:
                        continue

                    similarity = compute_cosine_similarity(
                        stu_vec, req_vec, expected_dim=stu_dim
                    )
                    if similarity is not None:
                        scored_pairs.append(
                            CandidatePair(
                                source_skill_id=stu_id,
                                target_skill_id=req_id,
                                similarity_score=similarity,
                            )
                        )

                eligible_candidates = filter_and_rank_candidates(
                    candidate_pairs=scored_pairs,
                    threshold=effective_threshold,
                    max_candidates=effective_max,
                )

                if not eligible_candidates:
                    discovery_run.status = "COMPLETED"
                    discovery_run.completed_at = datetime.now(UTC)
                    discovery_run.candidates_submitted_count = 0
                    await session.commit()
                    return discovery_run

                # Submit eligible candidate pairs to SSKS
                newly_submitted_count = 0
                failed_count = 0

                async def _perform_submissions(client: httpx.AsyncClient):
                    nonlocal newly_submitted_count, failed_count
                    for cand in eligible_candidates:
                        success, outcome = await submit_candidate_to_ssks(
                            client=client,
                            ssks_base_url=settings.ssks_base_url,
                            source_skill_id=cand.source_skill_id,
                            target_skill_id=cand.target_skill_id,
                            similarity_score=cand.similarity_score,
                            analysis_id=analysis_id,
                            max_retries=settings.candidate_discovery_max_retries,
                        )
                        if success:
                            if outcome == "CREATED":
                                newly_submitted_count += 1
                        else:
                            failed_count += 1

                if http_client is not None:
                    await _perform_submissions(http_client)
                else:
                    async with httpx.AsyncClient(
                        timeout=settings.candidate_discovery_timeout_seconds
                    ) as client:
                        await _perform_submissions(client)

                # Represent execution outcome accurately based on submission results
                if failed_count > 0:
                    if newly_submitted_count > 0:
                        final_status = "PARTIALLY_COMPLETED"
                    else:
                        final_status = "FAILED"
                else:
                    final_status = "COMPLETED"

                discovery_run.status = final_status
                discovery_run.candidates_submitted_count = newly_submitted_count
                discovery_run.completed_at = datetime.now(UTC)
                await session.commit()
                return discovery_run

            except Exception:
                await session.rollback()
                logger.exception(
                    "Unexpected error executing candidate discovery for analysis %s",
                    analysis_id,
                )
                try:
                    await session.execute(
                        update(CandidateDiscoveryRun)
                        .where(CandidateDiscoveryRun.id == run_id)
                        .values(
                            status="FAILED",
                            completed_at=datetime.now(UTC),
                        )
                    )
                    await session.commit()
                except Exception as update_err:  # noqa: BLE001
                    logger.error("Failed to persist run failure status: %s", update_err)
                return None
