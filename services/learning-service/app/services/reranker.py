import re
import json
import math
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from app.core.config import settings

# Cross-encoder (ms-marco-MiniLM-L6-v2 fine-tuned on the learning corpus, scripts/training/train_retrieval.py):
# on unseen documents it re-ranked the embedder's top 10 better than the rule-based scorer, which ranked
# worse than no re-ranking. Missing model files fall back to the rule-based scorer.
MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "reranker"


class ReRankerService:
    """
    Two-Stage Re-Ranking and Context Compression Service.
    Stage 1: Fetch Top-N candidates via Hybrid RRF (Dense + Sparse).
    Stage 2: Score cross-relevance, elevate best passages to Top-K, and compress context to avoid
    the 'Lost in the Middle' phenomenon and minimize prompt token overhead.
    """

    def __init__(self, model_dir: Path = MODEL_DIR):
        self.model_dir = model_dir
        self._session = None
        self._tokenizer = None
        self._inputs: List[str] = []
        self._unavailable = False

    def _load_model(self) -> bool:
        if self._session is None and not self._unavailable:
            try:
                import onnxruntime as ort
                from tokenizers import Tokenizer
                meta = json.loads((self.model_dir / "metadata.json").read_text())
                self._inputs = meta["inputs"]
                self._tokenizer = Tokenizer.from_file(str(self.model_dir / "tokenizer.json"))
                self._tokenizer.enable_truncation(meta["max_length"])
                self._tokenizer.enable_padding()
                self._session = ort.InferenceSession(str(self.model_dir / "model.onnx"),
                                                     providers=["CPUExecutionProvider"])
            except Exception as e:
                print(f"[Warning] Re-ranker model unavailable ({e}); using the rule-based scorer.")
                self._unavailable = True
        return self._session is not None

    def model_scores(self, query: str, candidates: List[Dict[str, Any]]) -> Optional[np.ndarray]:
        """Relevance 0-1 (sigmoid of the cross-encoder logit) per candidate, or None without a model."""
        if not self._load_model():
            return None
        enc = self._tokenizer.encode_batch([(query, item.get("content", "")) for item in candidates])
        feed = {"input_ids": [e.ids for e in enc], "attention_mask": [e.attention_mask for e in enc],
                "token_type_ids": [e.type_ids for e in enc]}
        logits = self._session.run(None, {n: np.asarray(feed[n], np.int64) for n in self._inputs})[0].reshape(-1)
        return 1.0 / (1.0 + np.exp(-logits))

    def rerank_candidates(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 3,
        use_model: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Re-ranks Top-N candidates (e.g. 10) down to Top-K (e.g. 3) with the cross-encoder, or without it
        (use_model=False or no model files) by multi-factor cross-relevance scoring: lexical term
        coverage, phrase alignment, title-topic affinity, and dense similarity fusion.
        """
        if not candidates:
            return []

        model_scores = None
        if use_model:
            try:
                model_scores = self.model_scores(query, candidates)
            except Exception as e:
                print(f"[Warning] Re-ranker model failed ({e}); using the rule-based scorer.")

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
            if model_scores is not None:
                normalized_score = round(float(model_scores[orig_rank - 1]), 4)

            scored_candidates.append({
                **item,
                "pre_rerank_rank": orig_rank,
                "rerank_score": normalized_score,
                "rerank_method": "cross_encoder" if model_scores is not None else "rule_based",
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
