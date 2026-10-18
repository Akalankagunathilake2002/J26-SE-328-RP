import hashlib
import json
from pathlib import Path
import numpy as np
from typing import List
from app.core.config import settings

SERVICE_ROOT = Path(__file__).resolve().parents[2]


class EmbeddingError(Exception):
    pass


class OnnxEmbedder:
    """The fine-tuned bge-small exported by scripts/training/train_retrieval.py (fastembed only loads its
    built-in models): the CLS vector of the last hidden state, normalised by EmbeddingService like fastembed's."""

    def __init__(self, model_dir: Path):
        import onnxruntime as ort
        from tokenizers import Tokenizer
        meta = json.loads((model_dir / "metadata.json").read_text())
        self._inputs = meta["inputs"]
        self._tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self._tokenizer.enable_truncation(meta["max_length"])
        self._tokenizer.enable_padding()
        self._session = ort.InferenceSession(str(model_dir / "model.onnx"), providers=["CPUExecutionProvider"])

    def embed(self, texts: List[str], batch_size: int = 32):
        for start in range(0, len(texts), batch_size):
            enc = self._tokenizer.encode_batch(texts[start:start + batch_size])
            feed = {"input_ids": [e.ids for e in enc], "attention_mask": [e.attention_mask for e in enc],
                    "token_type_ids": [e.type_ids for e in enc]}
            hidden = self._session.run(None, {n: np.asarray(feed[n], np.int64) for n in self._inputs})[0]
            yield from hidden[:, 0]


def _local_model_dir(name: str):
    """LOCAL_EMBEDDING_MODEL is a fastembed model name or a directory (relative to the service) holding an
    exported model; a directory that is missing is an error, not a silent switch to another model."""
    path = Path(name) if Path(name).is_absolute() else SERVICE_ROOT / name
    if path.is_dir():
        return path
    if name.startswith(("models/", "./", "/")):
        raise EmbeddingError(f"LOCAL_EMBEDDING_MODEL={name}: no exported model at {path}")
    return None


class EmbeddingService:
    """Embeds questions and queries for pgvector retrieval.

    Providers: "gemini", "openai", "local" (fastembed ONNX model in this container, no key) and
    "mock" (deterministic random vectors, for tests only). A real provider never silently falls
    back to random vectors: retrieval would quietly return random documents.
    """

    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.dimension = settings.EMBEDDING_DIMENSION
        self._client = None
        self._ready = False

    def _ensure_client(self):
        # Lazy, so a missing key or model shows up as a clear error on use, not a crash at import
        if not self._ready:
            self._init_client()
            self._ready = True

    def _init_client(self):
        if self.provider == "gemini":
            if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("your_"):
                raise EmbeddingError("EMBEDDING_PROVIDER=gemini needs GEMINI_API_KEY")
            from google import genai
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        elif self.provider == "openai":
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your_"):
                raise EmbeddingError("EMBEDDING_PROVIDER=openai needs OPENAI_API_KEY")
            from openai import OpenAI
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        elif self.provider == "local":
            model_dir = _local_model_dir(settings.LOCAL_EMBEDDING_MODEL)
            if model_dir:
                self._client = OnnxEmbedder(model_dir)
            else:
                from fastembed import TextEmbedding
                self._client = TextEmbedding(model_name=settings.LOCAL_EMBEDDING_MODEL)
            probe = len(next(iter(self._client.embed(["dimension probe"]))))
            if probe != self.dimension:
                raise EmbeddingError(
                    f"{settings.LOCAL_EMBEDDING_MODEL} produces {probe}-dimensional vectors but "
                    f"EMBEDDING_DIMENSION={self.dimension}; set EMBEDDING_DIMENSION={probe}"
                )

    def embed_text(self, text: str) -> List[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self.provider == "mock":
            return [self._generate_mock_embedding(t) for t in texts]
        self._ensure_client()
        try:
            if self.provider == "local":
                # Small batches keep ONNX Runtime's memory arena from growing with long documents
                return [self._normalise(np.asarray(v, dtype=np.float32))
                        for v in self._client.embed(texts, batch_size=32)]
            if self.provider == "gemini":
                from google.genai import types
                results = []
                for t in texts:
                    resp = self._client.models.embed_content(
                        model=settings.EMBEDDING_MODEL_NAME,
                        contents=t,
                        config=types.EmbedContentConfig(output_dimensionality=self.dimension)
                    )
                    results.append(self._normalise(np.array(resp.embeddings[0].values, dtype=np.float32)))
                return results
            res = self._client.embeddings.create(model=settings.EMBEDDING_MODEL_NAME, input=texts)
            return [d.embedding for d in res.data]
        except Exception as e:
            raise EmbeddingError(f"{self.provider} embedding failed: {e}") from e

    @staticmethod
    def _normalise(vec: np.ndarray) -> List[float]:
        norm = np.linalg.norm(vec)
        return (vec / norm if norm > 0 else vec).tolist()

    def _generate_mock_embedding(self, text: str) -> List[float]:
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        return self._normalise(rng.standard_normal(self.dimension))


embedding_service = EmbeddingService()
