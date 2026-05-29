import json
from pathlib import Path

from app.config import CANONICAL_DOCS_PATH
from app.retrieval import ACLContext, HybridRetriever


def load_docs():
    return json.loads(CANONICAL_DOCS_PATH.read_text(encoding="utf-8"))


def run_demo(
    query: str,
    user_team: str,
    user_role: str,
    user_clearance: str = "internal",
    top_k: int = 8,
):
    docs = load_docs()
    retriever = HybridRetriever(docs=docs)
    out = retriever.search(
        query=query,
        ctx=ACLContext(
            user_id="demo-user",
            team=user_team,
            role=user_role,
            clearance=user_clearance,
        ),
        top_k=top_k,
    )

    print(
        f"query='{out['query']}' total_docs={out['total_docs']} "
        f"allowed_docs={out['allowed_docs']} bm25={out['bm25_count']} dense={out['dense_count']}"
    )
    for i, row in enumerate(out["results"], 1):
        d = row["doc"]
        print(
            f"{i}. rrf={row['score']:.6f} source={d['source_type']} id={d['source_id']} "
            f"title={d['title']}"
        )


if __name__ == "__main__":
    run_demo(
        query="latest payments incident root cause and mitigation",
        user_team="payments",
        user_role="Senior Engineer",
        top_k=8,
    )
