import re
from typing import Any, Dict, List, Set

from app.retrieval.bm25 import BM25Retriever

KNOWN_CHANNELS = [
    "eng-platform",
    "incidents-warroom",
    "payments-ops",
    "search-ranking",
    "security-alerts",
    "eng-announcements",
]


def extract_channels_from_query(query: str) -> List[str]:
    lower = query.lower()
    found = [ch for ch in KNOWN_CHANNELS if ch in lower]
    return found


def doc_matches_channel(doc: Dict[str, Any], channel: str) -> bool:
    ch = channel.lower()
    title = (doc.get("title") or "").lower()
    content = (doc.get("content") or "").lower()
    tags = " ".join(doc.get("tags") or []).lower()
    blob = f"{title} {content} {tags}"
    return ch in blob


def channels_in_results(results: List[Dict[str, Any]]) -> Set[str]:
    found: Set[str] = set()
    for row in results:
        doc = row["doc"]
        for ch in KNOWN_CHANNELS:
            if doc_matches_channel(doc, ch):
                found.add(ch)
    return found


def channels_in_citations(citations: List[Dict[str, Any]]) -> Set[str]:
    found: Set[str] = set()
    for c in citations:
        title = (c.get("title") or "").lower()
        for ch in KNOWN_CHANNELS:
            if ch in title:
                found.add(ch)
    return found


def retrieve_per_channel(
    query: str,
    allowed_docs: List[Dict[str, Any]],
    channels: List[str],
    per_channel: int = 2,
) -> List[Dict[str, Any]]:
    """BM25 over each channel subset so multi-channel queries don't collapse to one channel."""
    picked: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    for channel in channels:
        subset = [d for d in allowed_docs if doc_matches_channel(d, channel)]
        if not subset:
            continue
        channel_query = f"{query} channel {channel} unresolved open action"
        bm25 = BM25Retriever()
        bm25.fit(subset)
        hits = bm25.search(channel_query, top_k=per_channel)
        for row in hits:
            doc_id = row["doc"]["doc_id"]
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)
            picked.append(row)

    return picked


def merge_with_channel_coverage(
    fused: List[Dict[str, Any]],
    allowed_docs: List[Dict[str, Any]],
    query: str,
    top_k: int,
) -> List[Dict[str, Any]]:
    channels = extract_channels_from_query(query)
    if len(channels) < 2:
        return fused[:top_k]

    channel_hits = retrieve_per_channel(query, allowed_docs, channels, per_channel=2)
    merged: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    # Guarantee at least one hit per requested channel (from channel-specific search)
    for ch in channels:
        for row in channel_hits:
            if row["doc"]["doc_id"] in seen:
                continue
            if doc_matches_channel(row["doc"], ch):
                merged.append(row)
                seen.add(row["doc"]["doc_id"])
                break

    # Add channel-specific hits
    for row in channel_hits:
        doc_id = row["doc"]["doc_id"]
        if doc_id not in seen:
            merged.append(row)
            seen.add(doc_id)

    # Fill from global fused ranking
    for row in fused:
        if len(merged) >= top_k:
            break
        doc_id = row["doc"]["doc_id"]
        if doc_id not in seen:
            merged.append(row)
            seen.add(doc_id)

    return merged[:top_k]
