"""Re-ranker: fine-tuned cross-encoder and rule-based fallback (app/services/reranker.py)."""
import pytest

from app.services.reranker import MODEL_DIR, ReRankerService

QUERY = "How do I make a Kubernetes volume read-only for one container?"
CANDIDATES = [
    {"chunk_id": 1, "content": "PostgreSQL B-Tree indexes support equality and range queries on sortable data.",
     "title": "Indexing", "topic": "Databases", "similarity_score": 0.62},
    {"chunk_id": 2, "content": "Set readOnly: true in the container's volumeMounts entry to mount the volume "
                               "read-only in that container; other containers can still mount it read-write.",
     "title": "Volumes", "topic": "Kubernetes Storage", "similarity_score": 0.60},
]


def test_missing_model_falls_back_to_rule_based(tmp_path):
    ranked = ReRankerService(model_dir=tmp_path).rerank_candidates(QUERY, CANDIDATES, top_k=2)
    assert [r["rerank_method"] for r in ranked] == ["rule_based", "rule_based"]
    assert ranked[0]["chunk_id"] == 2


def test_rule_based_can_be_forced():
    ranked = ReRankerService().rerank_candidates(QUERY, CANDIDATES, top_k=1, use_model=False)
    assert ranked[0]["rerank_method"] == "rule_based"


@pytest.mark.skipif(not (MODEL_DIR / "model.onnx").exists(), reason="re-ranker model not exported")
def test_cross_encoder_ranks_the_answering_passage_first():
    ranked = ReRankerService().rerank_candidates(QUERY, CANDIDATES, top_k=2)
    assert ranked[0]["chunk_id"] == 2 and ranked[0]["rerank_method"] == "cross_encoder"
    # Scores order candidates; their absolute level isn't calibrated (an answering passage can score < 0.5)
    assert ranked[0]["rerank_score"] > ranked[1]["rerank_score"]
    assert ranked[0]["final_rank"] == 1 and ranked[0]["rank_delta"] == 1
