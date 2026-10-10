import numpy as np
import pytest
from app.services.embedding_service import embedding_service


def test_embedding_dimension():
    vec = embedding_service.embed_text("How does connection pooling work in database drivers?")
    assert isinstance(vec, list)
    assert len(vec) == 1536
    # Verify vector is unit normalized (norm ≈ 1.0)
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-4


def test_embedding_batch():
    texts = [
        "First query about REST APIs",
        "Second query about PostgreSQL indexes",
        "Third query about JWT tokens"
    ]
    vectors = embedding_service.embed_batch(texts)
    assert len(vectors) == 3
    for v in vectors:
        assert len(v) == 1536
