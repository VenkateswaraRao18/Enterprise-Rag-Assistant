import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import (
    CANONICAL_DOCS_PATH,
    EMBED_BATCH_SIZE,
    EMBEDDING_META_PATH,
    LLM_PROVIDER,
    QDRANT_COLLECTION,
    QDRANT_UPSERT_BATCH_SIZE,
    QDRANT_URL,
)
from app.retrieval.embeddings import doc_to_embed_text
from app.retrieval.provider import embed_model_name, get_embedding_client
from app.retrieval.qdrant_store import QdrantVectorStore


def load_canonical_docs(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run ingestion first: python3 -m app.main"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def index_docs(docs, recreate: bool = False):
    embedder = get_embedding_client()
    store = QdrantVectorStore()

    sample_text = doc_to_embed_text(docs[0])
    sample_vector = embedder.embed_text(sample_text, task_type="RETRIEVAL_DOCUMENT")
    vector_size = len(sample_vector)

    store.ensure_collection(vector_size=vector_size, recreate=recreate)

    total_upserted = 0
    for i in range(0, len(docs), EMBED_BATCH_SIZE):
        batch = docs[i : i + EMBED_BATCH_SIZE]
        texts = [doc_to_embed_text(d) for d in batch]
        vectors = embedder.embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")

        for j in range(0, len(batch), QDRANT_UPSERT_BATCH_SIZE):
            sub_docs = batch[j : j + QDRANT_UPSERT_BATCH_SIZE]
            sub_vectors = vectors[j : j + QDRANT_UPSERT_BATCH_SIZE]
            total_upserted += store.upsert_points(sub_docs, sub_vectors)

        print(f"Indexed {min(i + EMBED_BATCH_SIZE, len(docs))}/{len(docs)} docs")

    meta = {
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "llm_provider": LLM_PROVIDER,
        "model": embed_model_name(),
        "vector_size": vector_size,
        "doc_count": len(docs),
        "qdrant_url": QDRANT_URL,
        "collection": QDRANT_COLLECTION,
        "points_in_collection": store.count_points(),
        "total_upserted": total_upserted,
    }
    EMBEDDING_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    EMBEDDING_META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(json.dumps(meta, indent=2))
    return meta


def main():
    parser = argparse.ArgumentParser(description="Embed canonical docs and upsert to Qdrant")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate Qdrant collection before indexing",
    )
    args = parser.parse_args()

    docs = load_canonical_docs(CANONICAL_DOCS_PATH)
    print(f"Loading {len(docs)} canonical docs from {CANONICAL_DOCS_PATH}")
    print(f"LLM_PROVIDER={LLM_PROVIDER} embed_model={embed_model_name()}")
    index_docs(docs, recreate=args.recreate)


if __name__ == "__main__":
    main()
