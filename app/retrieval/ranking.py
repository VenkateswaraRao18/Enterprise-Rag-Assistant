import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def recency_multiplier(updated_at: Any, half_life_days: float = 45.0) -> float:
    dt = _parse_dt(updated_at)
    if not dt:
        return 1.0
    age_days = max((datetime.now(timezone.utc) - dt).total_seconds() / 86400.0, 0.0)
    return 0.5 + 0.5 * math.exp(-age_days / half_life_days)


def intent_source_boost(query: str, doc: Dict[str, Any]) -> float:
    q = query.lower()
    source_type = doc.get("source_type", "")
    title = (doc.get("title") or "").lower()
    content = (doc.get("content") or "").lower()
    tags = " ".join(doc.get("tags") or []).lower()
    blob = f"{title} {content} {tags}"

    boost = 1.0

    jira_signals = ["jira", "ticket", "p0", "p1", "p2", "blocked", "open issue"]
    if source_type == "jira" and any(s in q for s in jira_signals):
        boost *= 1.4

    slack_signals = ["slack", "channel", "warroom", "eng-platform", "incidents-warroom", "chat"]
    if source_type == "slack" and any(s in q for s in slack_signals):
        boost *= 1.5
    if source_type == "slack" and "incidents-warroom" in q and "incidents-warroom" in blob:
        boost *= 1.4

    for channel in ("eng-platform", "incidents-warroom", "payments-ops", "security-alerts"):
        if channel in q and channel in blob:
            boost *= 1.65

    incident_signals = ["incident", "sev1", "sev2", "sev3", "postmortem", "outage", "root cause", "duration"]
    if source_type == "incident" and any(s in q for s in incident_signals):
        boost *= 1.5
    if source_type == "incident" and re.search(r"sev\s*1|sev1", q):
        boost *= 1.35

    oncall_signals = ["on-call", "oncall", "pager", "primary", "secondary", "handoff"]
    if source_type == "oncall" and any(s in q for s in oncall_signals):
        boost *= 1.4

    kb_signals = ["policy", "runbook", "playbook", "sop", "roadmap", "retention"]
    if source_type == "kb" and any(s in q for s in kb_signals):
        boost *= 1.35

    # Exact token presence in doc (helps P1, Blocked, SEV1, etc.)
    for token in re.findall(r"[a-zA-Z0-9_\-]+", q):
        if len(token) >= 3 and token in blob:
            boost *= 1.05

    if any(w in q for w in ["latest", "recent", "last week", "this week"]):
        boost *= recency_multiplier(doc.get("updated_at") or doc.get("timestamp"), half_life_days=21.0)

    return boost


def enhance_scores(results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    enhanced = []
    for row in results:
        doc = row["doc"]
        base = float(row.get("score", 0.0))
        mult = intent_source_boost(query, doc) * recency_multiplier(
            doc.get("updated_at") or doc.get("timestamp")
        )
        enhanced.append({**row, "score": base * mult})
    enhanced.sort(key=lambda x: x["score"], reverse=True)
    return enhanced


def diversify_top_k(
    results: List[Dict[str, Any]],
    top_k: int,
    max_per_source: int = 2,
) -> List[Dict[str, Any]]:
    """Keep top results while limiting chunks per source_type for cross-source coverage."""
    picked: List[Dict[str, Any]] = []
    per_source: Dict[str, int] = {}

    for row in results:
        st = row["doc"].get("source_type", "unknown")
        if per_source.get(st, 0) >= max_per_source:
            continue
        picked.append(row)
        per_source[st] = per_source.get(st, 0) + 1
        if len(picked) >= top_k:
            return picked

    # Backfill if diversity constraints left slots empty
    seen_ids = {r["doc"]["doc_id"] for r in picked}
    for row in results:
        if len(picked) >= top_k:
            break
        if row["doc"]["doc_id"] not in seen_ids:
            picked.append(row)
            seen_ids.add(row["doc"]["doc_id"])

    return picked
