"""Fast stand-ins for the AI models and the database, so tests run without them."""
import zlib

import numpy as np

DIM = 256


class WordEncoder:
    """Stand-in for the BERT encoder: a bag-of-words vector, so shared words mean similar."""

    model_name = "test-words"

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), DIM), dtype=np.float32)
        for row, text in enumerate(texts):
            for word in text.lower().replace(":", " ").replace(",", " ").split():
                vectors[row, zlib.crc32(word.encode()) % DIM] += 1
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.where(norms == 0, 1, norms)


class KeywordReranker:
    """Stand-in for the cross-encoder: prefers the candidate that contains a given word."""

    def __init__(self, keyword: str):
        self.keyword = keyword

    def score(self, query: str, texts: list[str]) -> list[float]:
        return [float(self.keyword in text.lower()) for text in texts]


class MemoryProfileStore:
    """Stand-in for the profile database: keeps saved profiles in a dict."""

    def __init__(self, broken: bool = False):
        self.profiles = {}
        self.broken = broken

    async def save(self, user_id, profile):
        from datetime import UTC, datetime

        if self.broken:
            raise OSError("database is down")
        saved_at = datetime.now(UTC)
        self.profiles[user_id] = profile.model_copy(update={"saved_at": saved_at})
        return saved_at

    async def load(self, user_id):
        if self.broken:
            raise OSError("database is down")
        return self.profiles.get(user_id)

    async def delete(self, user_id):
        if self.broken:
            raise OSError("database is down")
        return self.profiles.pop(user_id, None) is not None
