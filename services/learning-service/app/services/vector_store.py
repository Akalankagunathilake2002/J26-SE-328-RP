import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, cast, String
from app.models.learning import LearningChunk, LearningDocument
from app.services.embedding_service import embedding_service
from app.core.config import settings


class VectorStoreService:
    @staticmethod
    async def search_dense_chunks(
        session: AsyncSession,
        query: str,
        target_role: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Executes dense semantic vector search over learning_chunks using pgvector cosine distance.
        Applies role-based pre-filtering to ensure domain relevance.
        """
        query_vector = embedding_service.embed_text(query)
        distance_expr = LearningChunk.embedding.cosine_distance(query_vector).label("distance")

        stmt = (
            select(
                LearningChunk.id.label("chunk_id"),
                LearningChunk.content,
                LearningChunk.chunk_metadata,
                LearningDocument.title,
                LearningDocument.source,
                LearningDocument.url,
                LearningDocument.topic,
                LearningDocument.target_role,
                distance_expr
            )
            .join(LearningDocument, LearningChunk.document_id == LearningDocument.id)
        )

        if target_role and target_role.lower() != "all":
            stmt = stmt.where(
                or_(
                    LearningDocument.target_role.ilike(f"%{target_role}%"),
                    LearningDocument.target_role.ilike("%all%")
                )
            )

        stmt = stmt.order_by(distance_expr).limit(limit)
        result = await session.execute(stmt)
        rows = result.all()

        results = []
        for rank, row in enumerate(rows, 1):
            dist = float(row.distance) if row.distance is not None else 1.0
            similarity = max(0.0, min(1.0, 1.0 - dist))
            results.append({
                "chunk_id": str(row.chunk_id),
                "content": row.content,
                "title": row.title,
                "source": row.source,
                "url": row.url,
                "topic": row.topic,
                "target_role": row.target_role,
                "distance": dist,
                "similarity_score": round(similarity, 4),
                "dense_rank": rank,
                "metadata": row.chunk_metadata,
                "retrieval_method": "dense_vector"
            })
        return results

    @staticmethod
    async def search_sparse_chunks(
        session: AsyncSession,
        query: str,
        target_role: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Executes sparse lexical keyword search using PostgreSQL Full-Text Search (ts_rank_cd BM25 equivalent).
        Constructs a disjunctive token query (OR) to allow multi-term matching and coordinate relevance scoring.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        raw_ts_query = func.plainto_tsquery("english", clean_query)
        # Convert conjunction (&) to disjunction (|) for true multi-term BM25 scoring
        or_query_expr = func.to_tsquery("english", func.replace(cast(raw_ts_query, String), "&", "|"))
        ts_vector = func.to_tsvector("english", LearningChunk.content)
        sparse_score_expr = func.ts_rank_cd(ts_vector, or_query_expr).label("sparse_score")

        stmt = (
            select(
                LearningChunk.id.label("chunk_id"),
                LearningChunk.content,
                LearningChunk.chunk_metadata,
                LearningDocument.title,
                LearningDocument.source,
                LearningDocument.url,
                LearningDocument.topic,
                LearningDocument.target_role,
                sparse_score_expr
            )
            .join(LearningDocument, LearningChunk.document_id == LearningDocument.id)
            .where(ts_vector.op("@@")(or_query_expr))
        )

        if target_role and target_role.lower() != "all":
            stmt = stmt.where(
                or_(
                    LearningDocument.target_role.ilike(f"%{target_role}%"),
                    LearningDocument.target_role.ilike("%all%")
                )
            )

        stmt = stmt.order_by(sparse_score_expr.desc()).limit(limit)
        result = await session.execute(stmt)
        rows = result.all()

        results = []
        for rank, row in enumerate(rows, 1):
            score = float(row.sparse_score) if row.sparse_score is not None else 0.0
            results.append({
                "chunk_id": str(row.chunk_id),
                "content": row.content,
                "title": row.title,
                "source": row.source,
                "url": row.url,
                "topic": row.topic,
                "target_role": row.target_role,
                "sparse_score": round(score, 6),
                "similarity_score": min(1.0, round(score * 5.0, 4)),  # Normalized display score
                "sparse_rank": rank,
                "metadata": row.chunk_metadata,
                "retrieval_method": "sparse_bm25"
            })
        return results

    @classmethod
    async def search_hybrid_rrf(
        cls,
        session: AsyncSession,
        query: str,
        target_role: Optional[str] = None,
        top_k: int = 4,
        rrf_k: int = 60,
        w_dense: float = 0.5,
        w_sparse: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Executes state-of-the-art Hybrid Retrieval with Reciprocal Rank Fusion (RRF):
        RRF_Score(d) = (w_dense / (k + rank_dense(d))) + (w_sparse / (k + rank_sparse(d)))
        
        Merges dense semantic recall with exact sparse lexical precision.
        """
        pool_size = max(top_k * 3, 10)

        # 1. Fetch dense candidates
        dense_candidates = await cls.search_dense_chunks(
            session=session,
            query=query,
            target_role=target_role,
            limit=pool_size
        )

        # 2. Fetch sparse candidates
        sparse_candidates = await cls.search_sparse_chunks(
            session=session,
            query=query,
            target_role=target_role,
            limit=pool_size
        )

        # 3. Fuse via Reciprocal Rank Fusion (RRF)
        fused_chunks: Dict[str, Dict[str, Any]] = {}

        # Index dense ranks
        for item in dense_candidates:
            cid = item["chunk_id"]
            dense_rank = item["dense_rank"]
            fused_chunks[cid] = {
                **item,
                "dense_rank": dense_rank,
                "sparse_rank": None,
                "rrf_score": w_dense / (rrf_k + dense_rank)
            }

        # Index and fuse sparse ranks
        for item in sparse_candidates:
            cid = item["chunk_id"]
            sparse_rank = item["sparse_rank"]
            sparse_contrib = w_sparse / (rrf_k + sparse_rank)

            if cid in fused_chunks:
                fused_chunks[cid]["sparse_rank"] = sparse_rank
                fused_chunks[cid]["sparse_score"] = item.get("sparse_score", 0.0)
                fused_chunks[cid]["rrf_score"] += sparse_contrib
                fused_chunks[cid]["retrieval_method"] = "hybrid_fused (dense + sparse)"
            else:
                fused_chunks[cid] = {
                    **item,
                    "dense_rank": None,
                    "sparse_rank": sparse_rank,
                    "rrf_score": sparse_contrib,
                    "retrieval_method": "sparse_bm25_only"
                }

        # 4. Sort descending by RRF Score
        sorted_candidates = sorted(
            fused_chunks.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        # 5. Normalize RRF scores for client display and assign final hybrid ranks
        max_possible_rrf = (w_dense / (rrf_k + 1)) + (w_sparse / (rrf_k + 1))
        top_results = []
        for final_rank, item in enumerate(sorted_candidates[:top_k], 1):
            normalized_rrf = min(1.0, item["rrf_score"] / max_possible_rrf) if max_possible_rrf > 0 else 0.5
            item["hybrid_rank"] = final_rank
            item["rrf_score"] = round(item["rrf_score"], 6)
            # Use normalized RRF as similarity score for unified downstream pipeline
            item["similarity_score"] = round(normalized_rrf, 4)
            top_results.append(item)

        return top_results

    @classmethod
    async def search_learning_chunks(
        cls,
        session: AsyncSession,
        query: str,
        target_role: Optional[str] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Unified retrieval entrypoint adhering to settings.RETRIEVAL_STRATEGY.
        Defaults to Hybrid RRF.
        """
        strategy = settings.RETRIEVAL_STRATEGY
        if strategy == "dense_only":
            return await cls.search_dense_chunks(session, query, target_role, limit=top_k)
        elif strategy == "sparse_only":
            return await cls.search_sparse_chunks(session, query, target_role, limit=top_k)
        else:
            return await cls.search_hybrid_rrf(
                session=session,
                query=query,
                target_role=target_role,
                top_k=top_k,
                rrf_k=settings.RRF_K,
                w_dense=settings.DENSE_WEIGHT,
                w_sparse=settings.SPARSE_WEIGHT
            )

    @classmethod
    async def run_retrieval_ablation(
        cls,
        session: AsyncSession,
        query: str,
        target_role: Optional[str] = None,
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        Executes Dense-Only, Sparse-Only, and Hybrid-RRF in parallel
        and calculates Jaccard set overlap and rank agreement metrics for research publications.
        """
        # Dense
        t0 = time.perf_counter()
        dense_res = await cls.search_dense_chunks(session, query, target_role, limit=top_k)
        dense_lat = round((time.perf_counter() - t0) * 1000, 2)

        # Sparse
        t1 = time.perf_counter()
        sparse_res = await cls.search_sparse_chunks(session, query, target_role, limit=top_k)
        sparse_lat = round((time.perf_counter() - t1) * 1000, 2)

        # Hybrid RRF
        t2 = time.perf_counter()
        hybrid_res = await cls.search_hybrid_rrf(
            session=session,
            query=query,
            target_role=target_role,
            top_k=top_k,
            rrf_k=settings.RRF_K,
            w_dense=settings.DENSE_WEIGHT,
            w_sparse=settings.SPARSE_WEIGHT
        )
        hybrid_lat = round((time.perf_counter() - t2) * 1000, 2)

        dense_ids = set(x["chunk_id"] for x in dense_res)
        sparse_ids = set(x["chunk_id"] for x in sparse_res)
        hybrid_ids = set(x["chunk_id"] for x in hybrid_res)

        # Metrics
        union_ds = dense_ids | sparse_ids
        jaccard = round(len(dense_ids & sparse_ids) / len(union_ds), 4) if union_ds else 0.0
        hybrid_dense_agreement = round(len(hybrid_ids & dense_ids) / len(hybrid_ids), 4) if hybrid_ids else 0.0
        hybrid_sparse_agreement = round(len(hybrid_ids & sparse_ids) / len(hybrid_ids), 4) if hybrid_ids else 0.0

        return {
            "query": query,
            "target_role": target_role or "All",
            "dense": {
                "strategy": "dense_vector_only",
                "latency_ms": dense_lat,
                "count": len(dense_res),
                "chunks": dense_res,
                "topics": list(set(x["topic"] for x in dense_res))
            },
            "sparse": {
                "strategy": "sparse_bm25_fts_only",
                "latency_ms": sparse_lat,
                "count": len(sparse_res),
                "chunks": sparse_res,
                "topics": list(set(x["topic"] for x in sparse_res))
            },
            "hybrid": {
                "strategy": "hybrid_rrf_dense_sparse",
                "latency_ms": hybrid_lat,
                "count": len(hybrid_res),
                "chunks": hybrid_res,
                "topics": list(set(x["topic"] for x in hybrid_res))
            },
            "jaccard_overlap_dense_sparse": jaccard,
            "hybrid_dense_agreement": hybrid_dense_agreement,
            "hybrid_sparse_agreement": hybrid_sparse_agreement,
            "recommended_strategy": "hybrid_rrf"
        }


vector_store_service = VectorStoreService()
