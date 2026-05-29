"""Answer session / identity questions from the active ACL persona (no RAG)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.config import PROJECT_ROOT
from app.retrieval.acl import ACLContext, filter_acl_docs, is_employee

USERS_PATH = PROJECT_ROOT / "synthetic_data" / "techcorp" / "users.json"

IDENTITY_RE = re.compile(
    r"(?i)\b("
    r"who\s+am\s+i|who\s+iam|who\s+ami|whoami|"
    r"what(?:'s|\s+is)\s+my\s+(?:name|role|team|identity|clearance)|"
    r"which\s+(?:team|role)\s+am\s+i(?:\s+on)?|"
    r"my\s+(?:permissions?|access|identity|persona)|"
    r"what\s+can\s+i\s+access|"
    r"current\s+(?:user|identity|persona)|"
    r"about\s+me|"
    r"which\s+user\s+am\s+i"
    r")\b"
)

# Letter-only forms for typos / missing spaces ("who iam", "whoami").
_IDENTITY_COMPACT = frozenset(
    {
        "whoami",
        "whoiam",
        "whomi",
        "aboutme",
        "whatismyname",
        "whatismyrole",
        "whatismyteam",
        "whatismyclearance",
        "whatcaniaccess",
        "mypermissions",
        "myaccess",
        "myidentity",
    }
)

# Token sequences for short identity questions.
_IDENTITY_TOKEN_SEQS = frozenset(
    {
        ("who", "am", "i"),
        ("who", "iam"),
        ("who", "ami"),
        ("whoami",),
        ("about", "me"),
    }
)


def _letters_only(text: str) -> str:
    return re.sub(r"[^a-z]", "", text.lower())


def is_identity_query(query: str) -> bool:
    q = query.strip()
    if not q or len(q) > 160:
        return False
    if IDENTITY_RE.search(q):
        return True

    compact = _letters_only(q)
    if compact in _IDENTITY_COMPACT:
        return True

    tokens = re.findall(r"[a-z]+", q.lower())
    if tuple(tokens) in _IDENTITY_TOKEN_SEQS:
        return True

    # Very short queries that are only a who-am-i variant.
    if len(tokens) <= 3 and tokens and tokens[0] == "who":
        joined = "".join(tokens)
        if joined in {"whoami", "whoiam", "whoami", "whomi"}:
            return True

    return False


@lru_cache(maxsize=1)
def _load_users() -> List[Dict[str, Any]]:
    if not USERS_PATH.exists():
        return []
    return json.loads(USERS_PATH.read_text(encoding="utf-8"))


def _match_users(ctx: ACLContext) -> List[Dict[str, Any]]:
    return [
        u
        for u in _load_users()
        if u.get("team") == ctx.team and u.get("role") == ctx.role
    ]


def _empty_retrieval(docs: List[Dict[str, Any]], ctx: ACLContext) -> Dict[str, Any]:
    allowed = filter_acl_docs(docs, ctx)
    return {
        "total_docs": len(docs),
        "allowed_docs": len(allowed),
        "bm25_count": 0,
        "dense_count": 0,
        "results": [],
    }


def try_identity_answer(
    query: str,
    ctx: ACLContext,
    docs: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    if not is_identity_query(query):
        return None

    doc_list = docs or []
    retrieval = _empty_retrieval(doc_list, ctx)
    allowed = retrieval["allowed_docs"]
    matches = _match_users(ctx)

    lines: List[str] = []

    if ctx.team == "external":
        lines.append(
            "You are signed in as an **external Intern** persona (`team: external`). "
            "Most internal Slack, Jira, KB, and incident sources are **not** visible under ACL."
        )
    elif len(matches) == 1:
        u = matches[0]
        lines.append(
            f"You are **{u['name']}** — **{u['role']}** on the **{u['team']}** team."
        )
        lines.append(
            f"**Clearance:** {u.get('clearance', ctx.clearance)} · **Email:** {u['email']}"
        )
    elif len(matches) > 1:
        names = ", ".join(u["name"] for u in matches)
        lines.append(
            f"Your active session is **{ctx.role}** on **{ctx.team}** "
            f"(directory matches: {names})."
        )
    else:
        lines.append(
            f"Your active session is **{ctx.role}** on the **{ctx.team}** team "
            f"(clearance: **{ctx.clearance}**)."
        )

    if is_employee(ctx):
        lines.append(
            f"Under current ACL rules you can search **{allowed}** of **{retrieval['total_docs']}** "
            "indexed internal documents."
        )
    else:
        lines.append(
            f"Under current ACL rules you can search **{allowed}** of **{retrieval['total_docs']}** "
            "indexed documents (restricted external access)."
        )

    lines.append(
        "Operational questions (incidents, tickets, policies) are answered from retrieved evidence with citations."
    )

    return {
        "query": query,
        "answer": "\n".join(lines),
        "citations": [],
        "retrieval": retrieval,
        "abstained": False,
        "partial_evidence": False,
        "security_blocked": False,
        "security_category": None,
        "session_identity": True,
    }
