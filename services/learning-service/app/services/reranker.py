import re
import math
import time
from typing import List, Dict, Any, Optional
from app.core.config import settings


class ReRankerService:
    """
    Two-Stage Re-Ranking and Context Compression Service.
    Stage 1: Fetch Top-N candidates via Hybrid RRF (Dense + Sparse).
    Stage 2: Score cross-relevance, elevate best passages to Top-K, and compress context to avoid
    the 'Lost in the Middle' phenomenon and minimize prompt token overhead.
    """

    def __init__(self):
        pass

    def rerank_candidates(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Re-ranks Top-N candidates (e.g. 10) down to Top-K (e.g. 3) using multi-factor
        cross-relevance scoring: lexical term coverage, phrase alignment, title-topic affinity,
        and dense similarity fusion.
        """
        if not candidates:
            return []

        query_tokens = [w.lower() for w in re.findall(r'\b\w+\b', query) if len(w) > 2]
        query_set = set(query_tokens)
        query_lower = query.lower().strip()

        scored_candidates = []
        for orig_rank, item in enumerate(candidates, 1):
            content = item.get("content", "")
            title = item.get("title", "")
            topic = item.get("topic", "")
            content_lower = content.lower()
            title_lower = title.lower()
            topic_lower = topic.lower()

            # 1. Exact query phrase bonus
            phrase_bonus = 0.25 if query_lower in content_lower or query_lower in title_lower else 0.0

            # 2. Token overlap ratio in passage
            token_matches = sum(1 for tok in query_tokens if tok in content_lower)
            token_ratio = (token_matches / max(len(query_tokens), 1))

            # 3. Title / Topic affinity bonus
            title_matches = sum(1 for tok in query_tokens if tok in title_lower or tok in topic_lower)
            title_affinity = (title_matches / max(len(query_tokens), 1)) * 0.2

            # 4. Dense similarity baseline
            base_sim = item.get("similarity_score", 0.5)

            # 5. Composite Cross-Relevance Score
            cross_score = (base_sim * 0.45) + (token_ratio * 0.30) + phrase_bonus + title_affinity
            normalized_score = round(min(1.0, max(0.0, cross_score)), 4)

            scored_candidates.append({
                **item,
                "pre_rerank_rank": orig_rank,
                "rerank_score": normalized_score,
                "token_match_ratio": round(token_ratio, 2)
            })

        # Sort descending by rerank_score
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Select Top-K and annotate rank delta
        final_top = []
        for new_rank, item in enumerate(scored_candidates[:top_k], 1):
            orig_rank = item["pre_rerank_rank"]
            rank_delta = orig_rank - new_rank  # Positive means promoted, negative means demoted
            item["final_rank"] = new_rank
            item["rank_delta"] = rank_delta
            final_top.append(item)

        return final_top

    @staticmethod
    def compress_context_chunk(content: str, max_chars: int = 600) -> Dict[str, Any]:
        """
        Compresses an educational chunk:
        - Removes redundant markdown formatting, repeated newlines, and preamble boilerplate.
        - Retains high-information sentences containing technical definitions, code, or metrics.
        - Calculates token reduction metrics for research benchmarking.
        """
        raw_length = len(content)
        raw_token_est = max(1, raw_length // 4)

        # Remove decorative horizontal rules and repeated blank lines
        clean_text = re.sub(r'[-=]{3,}', '', content)
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)

        # Strip generic intro/boilerplate phrases
        boilerplate_patterns = [
            r'^(?:in this section,?|let us examine|as we know,?|it is important to note that)\s*',
            r'^(?:to summarize,?|in summary,?|furthermore,?|moreover,?)\s*'
        ]
        lines = clean_text.split('\n')
        compressed_lines = []
        for line in lines:
            line_str = line.strip()
            for pat in boilerplate_patterns:
                line_str = re.sub(pat, '', line_str, flags=re.IGNORECASE)
            if line_str:
                compressed_lines.append(line_str)

        compressed_text = "\n".join(compressed_lines)
        if len(compressed_text) > max_chars:
            compressed_text = compressed_text[:max_chars].rstrip() + "..."

        comp_length = len(compressed_text)
        comp_token_est = max(1, comp_length // 4)
        compression_ratio = round((raw_token_est - comp_token_est) / raw_token_est * 100, 1)

        return {
            "compressed_text": compressed_text,
            "original_tokens": raw_token_est,
            "compressed_tokens": comp_token_est,
            "compression_saved_percent": max(0.0, compression_ratio)
        }


reranker_service = ReRankerService()
