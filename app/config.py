import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_list(key: str, default: str) -> list[str]:
    raw = os.environ.get(key, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


# Provider: "ollama" (local) | "gemini" (AWS / production)
LLM_PROVIDER = _env("LLM_PROVIDER", "ollama").lower().strip()

# Ollama (local dev)
OLLAMA_BASE_URL = _env("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = _env("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_CHAT_MODEL = _env("OLLAMA_CHAT_MODEL", "gemma3:4b")

# Gemini (production)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_BASE = _env(
    "GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta"
)
GEMINI_CHAT_MODEL = _env("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
GEMINI_EMBED_MODEL = _env("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# Qdrant
QDRANT_URL = _env("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = _env("QDRANT_COLLECTION", "techcorp_docs")

# API server
API_HOST = _env("API_HOST", "0.0.0.0")
API_PORT = int(_env("API_PORT", "8080"))
CORS_ORIGINS = _env_list(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
)
# Optional: require X-API-Key header on POST /api/ask when set
API_KEY = os.environ.get("API_KEY", "")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DOCS_PATH = PROJECT_ROOT / "app" / "outputs" / "canonical_docs.json"
EMBEDDING_META_PATH = PROJECT_ROOT / "app" / "outputs" / "embedding_meta.json"

# Indexing
EMBED_BATCH_SIZE = int(_env("EMBED_BATCH_SIZE", "16"))
QDRANT_UPSERT_BATCH_SIZE = int(_env("QDRANT_UPSERT_BATCH_SIZE", "64"))
