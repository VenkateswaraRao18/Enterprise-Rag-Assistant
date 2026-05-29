from typing import List, Optional

import httpx

from app.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL


def doc_to_embed_text(doc: dict) -> str:
    parts = [
        doc.get("title", ""),
        doc.get("content", ""),
        " ".join(doc.get("tags", []) or []),
        " ".join(doc.get("entities", []) or []),
        doc.get("source_type", ""),
    ]
    return "\n".join(p for p in parts if p)


class OllamaEmbeddingClient:
    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_EMBED_MODEL,
        timeout: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def embed_text(self, text: str, task_type: Optional[str] = None) -> List[float]:
        del task_type  # Ollama ignores task type
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        payload = {"model": self.model, "prompt": text}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/embeddings", json=payload)
            resp.raise_for_status()
            data = resp.json()
        embedding = data.get("embedding")
        if not embedding:
            raise RuntimeError(f"Ollama returned no embedding for model={self.model}")
        return embedding

    def embed_texts(
        self,
        texts: List[str],
        task_type: Optional[str] = None,
    ) -> List[List[float]]:
        return [self.embed_text(t, task_type=task_type) for t in texts]
