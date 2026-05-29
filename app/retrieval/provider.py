"""Factory for LLM / embedding clients based on LLM_PROVIDER."""

from typing import Union

from app.config import LLM_PROVIDER
from app.retrieval.embeddings import OllamaEmbeddingClient
from app.retrieval.gemini_clients import GeminiChatClient, GeminiEmbeddingClient
from app.retrieval.generation import OllamaChatClient

EmbeddingClient = Union[OllamaEmbeddingClient, GeminiEmbeddingClient]
ChatClient = Union[OllamaChatClient, GeminiChatClient]


def get_embedding_client() -> EmbeddingClient:
    if LLM_PROVIDER == "gemini":
        return GeminiEmbeddingClient()
    return OllamaEmbeddingClient()


def get_chat_client() -> ChatClient:
    if LLM_PROVIDER == "gemini":
        return GeminiChatClient()
    return OllamaChatClient()


def embed_model_name() -> str:
    from app.config import GEMINI_EMBED_MODEL, OLLAMA_EMBED_MODEL

    if LLM_PROVIDER == "gemini":
        return GEMINI_EMBED_MODEL
    return OLLAMA_EMBED_MODEL
