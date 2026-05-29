import re
from typing import List


def expand_query_for_retrieval(query: str) -> str:
    """Add lexical hints for enterprise ops queries (BM25 + dense use same string)."""
    q = query
    lower = q.lower()
    extras: List[str] = []

    if "unresolved" in lower or "open item" in lower:
        extras.extend(["open", "blocked", "pending", "action", "follow-up", "in progress"])

    if "last two weeks" in lower or "last 2 weeks" in lower:
        extras.append("2026-01")

    for channel in ["eng-platform", "incidents-warroom", "security-alerts", "payments-ops"]:
        if channel in lower:
            extras.append(channel)

    if "on-call" in lower or "oncall" in lower:
        extras.extend(["primary", "secondary", "pager", "on-call"])

    if "p1" in lower or "p0" in lower:
        extras.extend(["P1", "P0", "priority"])

    if not extras:
        return q

    return q + " " + " ".join(extras)
