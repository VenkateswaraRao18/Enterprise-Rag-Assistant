import hashlib
import re
from datetime import datetime, timezone


def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def now_utc():
    return datetime.now(timezone.utc)


def build_doc_id(source_type: str, source_id: str, content_hash: str) -> str:
    return f"{source_type}:{source_id}:{content_hash[:12]}"


def extract_entities(text: str):
    if not text:
        return []
    patterns = [
        r"INC-\d+",
        r"\b(?:PAY|PLAT|SEARCH|SEC)-\d+\b",
        r"\b(?:payments-api|checkout-worker|search-indexer|feature-store|auth-gateway|deploy-orchestrator)\b",
    ]
    found = set()
    for p in patterns:
        for m in re.findall(p, text):
            found.add(m)
    return sorted(found)
