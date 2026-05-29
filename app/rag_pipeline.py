import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import CANONICAL_DOCS_PATH
from app.retrieval.acl import ACLContext
from app.retrieval.context import build_context_blocks
from app.retrieval.generation import build_rag_user_prompt
from app.retrieval.provider import ChatClient, get_chat_client
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.channel_retrieval import (
    channels_in_citations,
    extract_channels_from_query,
)
from app.retrieval.fallback_answer import build_channel_summary_fallback
from app.retrieval.query_expand import expand_query_for_retrieval
from app.security.input_guard import REFUSAL_MESSAGE, check_input
from app.security.output_guard import validate_output
from app.session_identity import try_identity_answer


class EnterpriseRAGPipeline:
    def __init__(
        self,
        docs: Optional[List[Dict[str, Any]]] = None,
        retriever: Optional[HybridRetriever] = None,
        chat_client: Optional[ChatClient] = None,
    ):
        if docs is None:
            docs = json.loads(CANONICAL_DOCS_PATH.read_text(encoding="utf-8"))
        self.docs = docs
        self.retriever = retriever or HybridRetriever(docs=docs)
        self.chat_client = chat_client or get_chat_client()

    def answer(
        self,
        query: str,
        ctx: ACLContext,
        top_k: int = 6,
        candidate_k: int = 20,
        min_evidence_blocks: int = 1,
    ) -> Dict[str, Any]:
        guard = check_input(query)
        if guard.blocked:
            return {
                "query": query,
                "answer": guard.reason or REFUSAL_MESSAGE,
                "citations": [],
                "retrieval": None,
                "abstained": True,
                "security_blocked": True,
                "security_category": guard.category,
            }

        identity = try_identity_answer(query, ctx, docs=self.docs)
        if identity is not None:
            return identity

        search_query = expand_query_for_retrieval(guard.sanitized_query or query)

        retrieval = self.retriever.search(
            query=search_query,
            ctx=ctx,
            top_k=top_k,
            candidate_k=candidate_k,
        )
        results = retrieval.get("results", [])
        context, citations = build_context_blocks(results)

        if len(citations) < min_evidence_blocks:
            return {
                "query": query,
                "answer": "Insufficient evidence in authorized sources.",
                "citations": [],
                "retrieval": retrieval,
                "abstained": True,
                "security_blocked": False,
                "security_category": None,
            }

        user_prompt = build_rag_user_prompt(search_query, context)
        raw_answer = self.chat_client.generate(user_prompt=user_prompt)

        out_guard = validate_output(raw_answer, citations, abstained=False)
        final_answer = out_guard.sanitized_answer if out_guard.sanitized_answer else raw_answer

        semantic_abstain = final_answer.strip().lower() == "insufficient evidence in authorized sources."

        required_channels = extract_channels_from_query(query)
        if semantic_abstain and citations and len(required_channels) >= 2:
            have = channels_in_citations(citations)
            if all(ch in have for ch in required_channels):
                final_answer = build_channel_summary_fallback(query, citations)
                semantic_abstain = False

        return {
            "query": query,
            "answer": final_answer,
            "citations": citations,
            "retrieval": retrieval,
            "abstained": semantic_abstain,
            "partial_evidence": not semantic_abstain and len(citations) > 0,
            "security_blocked": out_guard.blocked,
            "security_category": "output_guard" if out_guard.blocked else None,
            "security_note": out_guard.reason,
        }
