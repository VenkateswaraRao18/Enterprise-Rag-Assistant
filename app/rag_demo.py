import json

from app.rag_pipeline import EnterpriseRAGPipeline
from app.retrieval import ACLContext


def run_demo(
    query: str,
    user_team: str,
    user_role: str,
    user_clearance: str = "internal",
    top_k: int = 6,
):
    pipeline = EnterpriseRAGPipeline()
    out = pipeline.answer(
        query=query,
        ctx=ACLContext(
            user_id="demo-user",
            team=user_team,
            role=user_role,
            clearance=user_clearance,
        ),
        top_k=top_k,
    )

    print("=" * 80)
    print(f"QUERY: {out['query']}")
    print(f"USER: team={user_team} role={user_role} clearance={user_clearance}")
    print(f"ABSTAINED: {out['abstained']}")
    print("=" * 80)
    print("\nANSWER:\n")
    print(out["answer"])
    print("\nCITATIONS:")
    for c in out["citations"]:
        print(
            f"  [{c['ref']}] {c['source_type']}:{c['source_id']} | {c['title']} | {c.get('source_url')}"
        )
    print("\nRETRIEVAL STATS:")
    r = out["retrieval"]
    print(
        json.dumps(
            {
                "total_docs": r["total_docs"],
                "allowed_docs": r["allowed_docs"],
                "bm25_count": r["bm25_count"],
                "dense_count": r["dense_count"],
                "fused_count": len(r["results"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    run_demo(
        query="What was the latest payments-api incident root cause and mitigation?",
        user_team="payments",
        user_role="Senior Engineer",
        top_k=6,
    )
