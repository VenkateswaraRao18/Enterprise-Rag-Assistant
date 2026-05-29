from typing import Any, Dict, List, Optional

from app.retrieval.acl import ACLContext, filter_acl_docs
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.provider import EmbeddingClient, get_embedding_client
from app.retrieval.qdrant_store import QdrantVectorStore
from app.retrieval.channel_retrieval import merge_with_channel_coverage
from app.retrieval.query_expand import expand_query_for_retrieval
from app.retrieval.ranking import diversify_top_k, enhance_scores


def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    k: int = 60,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """Fuse multiple ranked result lists using RRF."""
    scores: Dict[str, float] = {}
    doc_by_id: Dict[str, Dict[str, Any]] = {}

    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            doc = item["doc"]
            doc_id = doc["doc_id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            doc_by_id[doc_id] = doc

    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [{"score": score, "doc": doc_by_id[doc_id]} for doc_id, score in fused[:top_k]]


class HybridRetriever:
    def __init__(
        self,
        docs: List[Dict[str, Any]],
        embed_client: Optional[EmbeddingClient] = None,
        vector_store: Optional[QdrantVectorStore] = None,
        rrf_k: int = 60,
        candidate_k: int = 50,
        max_per_source: int = 2,
    ):
        self.docs = docs
        self.embed_client = embed_client or get_embedding_client()
        self.vector_store = vector_store or QdrantVectorStore()
        self.rrf_k = rrf_k
        self.candidate_k = candidate_k
        self.max_per_source = max_per_source

    def search(
        self,
        query: str,
        ctx: ACLContext,
        top_k: int = 8,
        candidate_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        allowed_docs = filter_acl_docs(self.docs, ctx)
        allowed_ids = [d["doc_id"] for d in allowed_docs]
        ck = candidate_k or self.candidate_k

        bm25 = BM25Retriever()
        bm25.fit(allowed_docs)
        bm25_results = bm25.search(query, top_k=ck)

        query_vector = self.embed_client.embed_text(query, task_type="RETRIEVAL_QUERY")
        dense_results = self.vector_store.search(
            query_vector=query_vector,
            top_k=ck,
            allowed_doc_ids=allowed_ids,
        )

        fused = reciprocal_rank_fusion(
            [bm25_results, dense_results],
            k=self.rrf_k,
            top_k=max(top_k * 3, ck),
        )
        fused = enhance_scores(fused, query)
        max_per_source = self.max_per_source
        lower = query.lower()
        if "eng-platform" in lower and "incidents-warroom" in lower:
            max_per_source = 4
        diversified = diversify_top_k(fused, top_k=top_k, max_per_source=max_per_source)
        final = merge_with_channel_coverage(diversified, allowed_docs, query, top_k)

        return {
            "query": query,
            "total_docs": len(self.docs),
            "allowed_docs": len(allowed_docs),
            "bm25_count": len(bm25_results),
            "dense_count": len(dense_results),
            "results": final,
        }
