import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

CITATION_RE = re.compile(r"\[(\d+)\]")

_OUTPUT_BLOCK_PATTERNS = [
    re.compile(r"\bhere\s+are\s+all\s+documents\b", re.I),
    re.compile(r"\bvisibility\s+restricted\s+documents?\s*:", re.I),
    re.compile(r"\bsystem\s+prompt\s+is\b", re.I),
    re.compile(r"\bmy\s+instructions\s+are\b", re.I),
    re.compile(r"\bdebug\s+mode\s+enabled\b", re.I),
    re.compile(r"\bcitations?\s+disabled\b", re.I),
]


@dataclass
class OutputGuardResult:
    allowed: bool
    reason: Optional[str] = None
    sanitized_answer: Optional[str] = None

    @property
    def blocked(self) -> bool:
        return not self.allowed


def validate_output(
    answer: str,
    citations: List[Dict[str, Any]],
    abstained: bool = False,
) -> OutputGuardResult:
    if abstained:
        return OutputGuardResult(allowed=True, sanitized_answer=answer)

    text = (answer or "").strip()
    if not text:
        return OutputGuardResult(
            allowed=False,
            reason="Empty model response.",
            sanitized_answer="Insufficient evidence in authorized sources.",
        )

    for pattern in _OUTPUT_BLOCK_PATTERNS:
        if pattern.search(text):
            return OutputGuardResult(
                allowed=False,
                reason="Output matched unsafe exfiltration or policy-bypass language.",
                sanitized_answer=(
                    "I can't provide that response. Ask a specific operational question; "
                    "I'll answer only from authorized evidence with citations."
                ),
            )

    max_ref = len(citations)
    if max_ref == 0:
        if CITATION_RE.search(text) and "insufficient evidence" not in text.lower():
            return OutputGuardResult(
                allowed=False,
                reason="Citations present but no evidence blocks were retrieved.",
                sanitized_answer="Insufficient evidence in authorized sources.",
            )
        return OutputGuardResult(allowed=True, sanitized_answer=answer)

    # Invalid citation indices
    for match in CITATION_RE.finditer(text):
        ref = int(match.group(1))
        if ref < 1 or ref > max_ref:
            return OutputGuardResult(
                allowed=False,
                reason=f"Citation [{ref}] out of range (1-{max_ref}).",
                sanitized_answer=(
                    "I couldn't validate citations for this answer. "
                    "Please retry with a more specific question."
                ),
            )

    return OutputGuardResult(allowed=True, sanitized_answer=answer)
