"""Google Gemini API clients (Generative Language API)."""

from typing import List, Optional

import httpx

from app.config import (
    GEMINI_API_BASE,
    GEMINI_API_KEY,
    GEMINI_CHAT_MODEL,
    GEMINI_EMBED_MODEL,
)
from app.retrieval.generation import SYSTEM_PROMPT


class GeminiEmbeddingClient:
    def __init__(
        self,
        api_key: str = GEMINI_API_KEY,
        model: str = GEMINI_EMBED_MODEL,
        base_url: str = GEMINI_API_BASE,
        timeout: float = 120.0,
    ):
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when LLM_PROVIDER=gemini. "
                "Set it in the environment or AWS Secrets Manager."
            )
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def embed_text(
        self,
        text: str,
        task_type: Optional[str] = "RETRIEVAL_QUERY",
    ) -> List[float]:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        model_path = self.model if self.model.startswith("models/") else f"models/{self.model}"
        url = f"{self.base_url}/{model_path}:embedContent"

        body: dict = {
            "model": model_path,
            "content": {"parts": [{"text": text}]},
        }
        if task_type:
            body["taskType"] = task_type

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, params={"key": self.api_key}, json=body)
            resp.raise_for_status()
            data = resp.json()

        embedding = data.get("embedding", {}).get("values")
        if not embedding:
            raise RuntimeError(f"Gemini returned no embedding for model={self.model}")
        return embedding

    def embed_texts(
        self,
        texts: List[str],
        task_type: Optional[str] = "RETRIEVAL_DOCUMENT",
    ) -> List[List[float]]:
        return [self.embed_text(t, task_type=task_type) for t in texts]


class GeminiChatClient:
    def __init__(
        self,
        api_key: str = GEMINI_API_KEY,
        model: str = GEMINI_CHAT_MODEL,
        base_url: str = GEMINI_API_BASE,
        timeout: float = 120.0,
    ):
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when LLM_PROVIDER=gemini. "
                "Set it in the environment or AWS Secrets Manager."
            )
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(
        self,
        user_prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> str:
        model_path = self.model if self.model.startswith("models/") else f"models/{self.model}"
        url = f"{self.base_url}/{model_path}:generateContent"

        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
            },
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, params={"key": self.api_key}, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates for model={self.model}")

        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            raise RuntimeError(f"Gemini chat returned empty content for model={self.model}")
        return text
