from typing import Any, Dict, List, Tuple


def build_context_blocks(
    results: List[Dict[str, Any]],
    max_chars: int = 12000,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Turn retrieval hits into numbered evidence blocks for the LLM."""
    blocks: List[str] = []
    citations: List[Dict[str, Any]] = []
    used_chars = 0

    for i, row in enumerate(results, start=1):
        doc = row["doc"]
        source_type = doc.get("source_type", "")
        source_id = doc.get("source_id", "")
        title = doc.get("title", "")
        content = doc.get("content", "")
        source_url = doc.get("source_url")
        timestamp = doc.get("timestamp", "")

        block = (
            f"[{i}] source={source_type} id={source_id}\n"
            f"title: {title}\n"
            f"timestamp: {timestamp}\n"
            f"url: {source_url or 'n/a'}\n"
            f"content: {content}\n"
        )

        if used_chars + len(block) > max_chars:
            break

        blocks.append(block)
        used_chars += len(block)
        citations.append(
            {
                "ref": i,
                "doc_id": doc.get("doc_id"),
                "source_type": source_type,
                "source_id": source_id,
                "title": title,
                "source_url": source_url,
                "timestamp": timestamp,
                "rrf_score": row.get("score"),
            }
        )

    return "\n".join(blocks), citations
