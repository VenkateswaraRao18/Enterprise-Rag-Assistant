import json
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import API_KEY, CORS_ORIGINS, LLM_PROVIDER, PROJECT_ROOT
from app.rag_pipeline import EnterpriseRAGPipeline
from app.retrieval import ACLContext

USERS_PATH = PROJECT_ROOT / "synthetic_data" / "techcorp" / "users.json"


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    team: str = "platform"
    role: str = "SRE"
    clearance: str = "internal"
    top_k: int = Field(default=6, ge=1, le=20)


class CitationOut(BaseModel):
    ref: int
    doc_id: Optional[str] = None
    source_type: str
    source_id: str
    title: str
    source_url: Optional[str] = None
    timestamp: Optional[str] = None


class RetrievalStatsOut(BaseModel):
    total_docs: int
    allowed_docs: int
    bm25_count: int
    dense_count: int
    fused_count: int


class AskResponse(BaseModel):
    query: str
    answer: str
    abstained: bool
    citations: List[CitationOut]
    stats: RetrievalStatsOut
    security_blocked: bool = False
    security_category: Optional[str] = None


class PersonaOption(BaseModel):
    label: str
    team: str
    role: str
    clearance: str = "internal"


def verify_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


@lru_cache(maxsize=1)
def get_pipeline() -> EnterpriseRAGPipeline:
    return EnterpriseRAGPipeline()


app = FastAPI(
    title="TechCorp Internal Knowledge Assistant",
    description="ACL-aware hybrid RAG over Slack, Jira, KB, and incidents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "techcorp-rag-api",
        "llm_provider": LLM_PROVIDER,
    }


@app.get("/api/personas", response_model=List[PersonaOption])
def list_personas():
    if not USERS_PATH.exists():
        return [
            PersonaOption(label="Platform SRE", team="platform", role="SRE"),
            PersonaOption(label="Payments Engineer", team="payments", role="Senior Engineer"),
            PersonaOption(label="VP Engineering", team="platform", role="VP Engineering"),
            PersonaOption(label="Unauthorized Intern", team="external", role="Intern"),
        ]
    users = json.loads(USERS_PATH.read_text(encoding="utf-8"))
    personas = []
    for u in users:
        personas.append(
            PersonaOption(
                label=f"{u['name']} ({u['role']}, {u['team']})",
                team=u["team"],
                role=u["role"],
                clearance=u.get("clearance", "internal"),
            )
        )
    personas.append(
        PersonaOption(
            label="Unauthorized Intern (external)",
            team="external",
            role="Intern",
            clearance="internal",
        )
    )
    return personas


@app.post("/api/ask", response_model=AskResponse, dependencies=[Depends(verify_api_key)])
def ask(req: AskRequest):
    try:
        pipeline = get_pipeline()
        ctx = ACLContext(
            user_id="web-user",
            team=req.team,
            role=req.role,
            clearance=req.clearance,
        )
        result = pipeline.answer(query=req.query, ctx=ctx, top_k=req.top_k)
    except Exception as exc:
        provider_hint = "Gemini and Qdrant" if LLM_PROVIDER == "gemini" else "Ollama and Qdrant"
        raise HTTPException(
            status_code=503,
            detail=f"RAG pipeline unavailable: {exc}. Ensure {provider_hint} are configured.",
        ) from exc

    retrieval = result.get("retrieval") or {}
    citations = [
        CitationOut(
            ref=c["ref"],
            doc_id=c.get("doc_id"),
            source_type=c.get("source_type", ""),
            source_id=c.get("source_id", ""),
            title=c.get("title", ""),
            source_url=c.get("source_url"),
            timestamp=c.get("timestamp"),
        )
        for c in result.get("citations", [])
    ]

    return AskResponse(
        query=result["query"],
        answer=result["answer"],
        abstained=result.get("abstained", False),
        citations=citations,
        stats=RetrievalStatsOut(
            total_docs=retrieval.get("total_docs", 0),
            allowed_docs=retrieval.get("allowed_docs", 0),
            bm25_count=retrieval.get("bm25_count", 0),
            dense_count=retrieval.get("dense_count", 0),
            fused_count=len(retrieval.get("results", [])),
        ),
        security_blocked=result.get("security_blocked", False),
        security_category=result.get("security_category"),
    )


@app.get("/api/example-queries")
def example_queries():
    return [
        "What was the latest payments-api incident root cause and mitigation?",
        "Who is on-call for the payments team this week?",
        "What are the top open P1 issues for payments?",
        "Summarize the on-call escalation policy acknowledgement targets.",
        "As VP Engineering, what are Q2 roadmap priorities?",
    ]
