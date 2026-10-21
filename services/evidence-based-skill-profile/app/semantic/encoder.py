"""Sentence embeddings: text → meaning vector (TAF tasks 4 and 5).

A pretrained BERT-family sentence-transformer turns a phrase into a vector, so phrases with the
same meaning ("made neural networks", "Deep Learning") get vectors pointing the same way. Vectors
are L2-normalised, so the inner product of two vectors is their cosine similarity (-1 to 1).
"""
from functools import lru_cache
from typing import Protocol

import numpy as np

from app.config.settings import get_settings


class Encoder(Protocol):
    model_name: str

    def encode(self, texts: list[str]) -> np.ndarray:
        """One normalised float32 row per text."""
        ...


class SentenceEncoder:
    def __init__(self, model_name: str, batch_size: int = 64):
        from sentence_transformers import SentenceTransformer  # heavy import, load on first use

        self.model_name = model_name
        self.batch_size = batch_size
        self._model = SentenceTransformer(model_name, device="cpu")

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = self._model.encode(
            texts, batch_size=self.batch_size, normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=len(texts) > 1000,
        )
        return np.asarray(vectors, dtype=np.float32)


@lru_cache
def get_encoder() -> SentenceEncoder:
    return SentenceEncoder(get_settings().embedding_model)
