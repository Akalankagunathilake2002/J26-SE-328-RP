"""Local embedding model loading (app/services/embedding_service.py)."""
import numpy as np
import pytest

from app.services.embedding_service import SERVICE_ROOT, EmbeddingError, OnnxEmbedder, _local_model_dir

MODEL_DIR = SERVICE_ROOT / "models" / "embedder"


def test_fastembed_names_are_not_paths():
    assert _local_model_dir("BAAI/bge-small-en-v1.5") is None


def test_missing_model_directory_is_an_error():
    with pytest.raises(EmbeddingError):
        _local_model_dir("models/no-such-embedder")


@pytest.mark.skipif(not (MODEL_DIR / "model.onnx").exists(), reason="embedder not exported")
def test_onnx_embedder_gives_384_dimensions_and_ranks_by_meaning():
    vecs = [v / np.linalg.norm(v) for v in OnnxEmbedder(MODEL_DIR).embed([
        "How do I speed up queries on a large table?",
        "Add an index on the columns used in WHERE clauses so the database avoids full table scans.",
        "Use a slogan that is short and memorable in your marketing campaign.",
    ])]
    assert all(len(v) == 384 for v in vecs)
    assert vecs[0] @ vecs[1] > vecs[0] @ vecs[2]


@pytest.mark.skipif(not (MODEL_DIR / "model.onnx").exists(), reason="embedder not exported")
def test_onnx_embedder_batches_match_single_texts():
    embedder = OnnxEmbedder(MODEL_DIR)
    texts = ["short", "a much longer sentence that needs padding when batched with a short one"]
    batched = list(embedder.embed(texts))
    for text, vec in zip(texts, batched):
        assert np.allclose(next(embedder.embed([text])), vec, atol=1e-4)
