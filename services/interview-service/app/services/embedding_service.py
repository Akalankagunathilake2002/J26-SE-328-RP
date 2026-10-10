import hashlib
import numpy as np
from typing import List
from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.dimension = settings.EMBEDDING_DIMENSION
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.provider == "gemini" and settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                from google import genai
                self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                print(f"[Warning] Google GenAI embedding init failed: {e}. Fallback to mock.")
                self.provider = "mock"
        elif self.provider == "openai" and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                print(f"[Warning] OpenAI embedding init failed: {e}. Fallback to deterministic mock.")
                self.provider = "mock"
        else:
            self.provider = "mock"

    def embed_text(self, text: str) -> List[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self.provider == "gemini" and self._client:
            try:
                from google.genai import types
                results = []
                for t in texts:
                    resp = self._client.models.embed_content(
                        model=settings.EMBEDDING_MODEL_NAME,
                        contents=t,
                        config=types.EmbedContentConfig(output_dimensionality=self.dimension)
                    )
                    vec = np.array(resp.embeddings[0].values, dtype=np.float32)
                    norm = np.linalg.norm(vec)
                    if norm > 0:
                        vec = vec / norm
                    results.append(vec.tolist())
                return results
            except Exception as e:
                print(f"[Error] Gemini embedding API call failed: {e}. Fallback to mock.")
                return [self._generate_mock_embedding(t) for t in texts]
        if self.provider == "openai" and self._client:
            try:
                res = self._client.embeddings.create(model=settings.EMBEDDING_MODEL_NAME, input=texts)
                return [d.embedding for d in res.data]
            except Exception as e:
                print(f"[Error] OpenAI API call failed: {e}. Fallback to mock.")
                return [self._generate_mock_embedding(t) for t in texts]
        return [self._generate_mock_embedding(t) for t in texts]

    def _generate_mock_embedding(self, text: str) -> List[float]:
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.dimension)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


embedding_service = EmbeddingService()
