"""Client for a local LLM served on the host Mac (mlx_lm.server, OpenAI-compatible API).

Used when LLM_PROVIDER=local, so the interview needs no cloud API key. The server runs on the
host because it needs the Apple GPU, which Docker can't use (see Huggingbay/start-llm.sh).
"""
import json
import re
from typing import Any, Dict, List

import httpx

from app.core.config import settings


class LocalLLMError(Exception):
    pass


class LocalLLM:
    def __init__(self):
        self._model_id: str | None = None

    @property
    def base(self) -> str:
        return settings.LOCAL_LLM_URL.rstrip("/")

    async def _model(self, client: httpx.AsyncClient) -> str:
        # mlx_lm.server tries to load whatever "model" names, so always use the one it already has
        if self._model_id is None:
            res = await client.get(f"{self.base}/v1/models")
            res.raise_for_status()
            self._model_id = res.json()["data"][0]["id"]
        return self._model_id

    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3,
                   max_tokens: int = 700) -> str:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(settings.LOCAL_LLM_TIMEOUT, connect=5.0)) as client:
                payload = {"model": await self._model(client), "messages": messages,
                           "temperature": temperature, "max_tokens": max_tokens,
                           # Models with a thinking mode (Gemma 4, Qwen3) otherwise spend most of the
                           # token budget reasoning: 10x slower and truncated JSON. Others ignore it.
                           "chat_template_kwargs": {"enable_thinking": settings.LOCAL_LLM_THINKING}}
                res = await client.post(f"{self.base}/v1/chat/completions", json=payload)
        except httpx.HTTPError as e:
            self._model_id = None               # the server may have been restarted with another model
            raise LocalLLMError(f"Local LLM unreachable at {self.base}: {e}") from e
        if res.status_code != 200:
            self._model_id = None
            raise LocalLLMError(f"Local LLM error ({res.status_code}): {res.text[:300]}")
        text = res.json()["choices"][0]["message"]["content"] or ""
        # Reasoning models wrap their thinking in <think>…</think>; only the answer is wanted
        return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()

    async def chat_json(self, system: str, user: str, temperature: float = 0.2,
                        max_tokens: int = 900) -> Dict[str, Any]:
        """Asks for a JSON object and extracts it even if the model adds prose or code fences."""
        text = await self.chat(
            [{"role": "system", "content": system + "\nRespond with the JSON object only."},
             {"role": "user", "content": user}],
            temperature=temperature, max_tokens=max_tokens,
        )
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise LocalLLMError(f"Local LLM did not return JSON: {text[:200]}")
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError as e:
            raise LocalLLMError(f"Local LLM returned invalid JSON: {e}") from e


local_llm = LocalLLM()
