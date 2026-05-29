import json
from pathlib import Path

from app.retrieval import ACLContext, BM25Retriever, filter_acl_docs


def load_docs(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_demo(query: str, user_team: str, user_role: str, user_clearance: str = "internal", top_k: int = 8):
    docs = load_docs(Path("app/outputs/canonical_docs.json"))
    ctx = ACLContext(user_id="demo-user", team=user_team, role=user_role, clearance=user_clearance)

    allowed_docs = filter_acl_docs(docs, ctx)

    retriever = BM25Retriever()
    retriever.fit(allowed_docs)
    results = retriever.search(query=query, top_k=top_k)

    print(f"total_docs={len(docs)} allowed_docs={len(allowed_docs)} query='{query}'")
    for i, row in enumerate(results, 1):
        d = row["doc"]
        print(
            f"{i}. score={row['score']} source={d['source_type']} id={d['source_id']} "
            f"title={d['title']} url={d.get('source_url')}"
        )


if __name__ == "__main__":
    # Example:
    run_demo(
        query="latest payments incident root cause and mitigation",
        user_team="payments",
        user_role="Senior Engineer",
        user_clearance="internal",
        top_k=8,
    )
