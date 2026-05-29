from typing import Any, Dict, List

from app.retrieval.channel_retrieval import KNOWN_CHANNELS, doc_matches_channel


def build_channel_summary_fallback(query: str, citations: List[Dict[str, Any]]) -> str:
    """Deterministic summary when LLM over-abstains but channel evidence exists."""
    by_channel: Dict[str, List[Dict[str, Any]]] = {}
    for c in citations:
        title = (c.get("title") or "").lower()
        matched = "other"
        for ch in KNOWN_CHANNELS:
            if ch in title or doc_matches_channel(
                {"title": c.get("title", ""), "content": "", "tags": c.get("tags", [])},
                ch,
            ):
                matched = ch
                break
        by_channel.setdefault(matched, []).append(c)

    lines = [
        "Summary from authorized sources (operational updates; items may not be labeled 'unresolved'):",
        "",
    ]
    for ch, items in sorted(by_channel.items()):
        lines.append(f"**{ch}**")
        for item in items:
            ref = item.get("ref", "?")
            title = item.get("title", "untitled")
            # Shorten title for readability
            parts = [p.strip() for p in title.split("|")]
            snippet = parts[1] if len(parts) > 1 else title
            lines.append(f"- {snippet} [{ref}]")
        lines.append("")

    if "two weeks" in query.lower() or "last two weeks" in query.lower():
        lines.append(
            "_Note: Evidence timestamps may not cover the full two-week window; "
            "synthetic corpus has fixed date ranges._"
        )

    return "\n".join(lines).strip()
