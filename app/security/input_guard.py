import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


REFUSAL_MESSAGE = (
    "I can't change safety or access settings in chat, and I can't export documents by "
    "visibility or role. Ask a specific work question (incident, ticket, runbook, on-call), "
    "and I'll answer only from sources you're authorized to see."
)


@dataclass
class InputGuardResult:
    allowed: bool
    category: Optional[str] = None
    reason: Optional[str] = None
    sanitized_query: str = ""

    @property
    def blocked(self) -> bool:
        return not self.allowed


# (compiled_pattern, category)
_BLOCK_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bignore\s+(all\s+)?(previous|prior)\s+instructions\b", re.I), "instruction_override"),
    (re.compile(r"\b(disregard|forget)\s+(all\s+)?(previous|prior)\s+instructions\b", re.I), "instruction_override"),
    (re.compile(r"\byou\s+are\s+now\b", re.I), "instruction_override"),
    (re.compile(r"\b(new|updated)\s+instructions?\s*:", re.I), "instruction_override"),
    (re.compile(r"^\s*system\s*:", re.I | re.M), "fake_system_role"),
    (re.compile(r"^\s*admin\s*:", re.I | re.M), "fake_system_role"),
    (re.compile(r"\bdebug\s+mode\b", re.I), "policy_bypass"),
    (re.compile(r"\bdisable\s+(citation|grounding|safety)\b", re.I), "policy_bypass"),
    (re.compile(r"\bno\s+citations?\s+required\b", re.I), "policy_bypass"),
    (re.compile(r"\banswer\s+from\s+general\s+knowledge\b", re.I), "policy_bypass"),
    (re.compile(r"\b(pentest|penetration\s+test)\s+authorized\b", re.I), "fake_authorization"),
    (re.compile(r"\bauthorized\s+by\s+(security|admin)\b", re.I), "fake_authorization"),
    (re.compile(r"\boverride\s+(acl|access|permissions?)\b", re.I), "fake_authorization"),
    (re.compile(r"\bdisable\s+(acl|access\s+control)\b", re.I), "fake_authorization"),
    (re.compile(r"\b(full|complete)\s+access\s+(for|granted|approved)\b", re.I), "fake_authorization"),
    (re.compile(r"\b(hiring\s+manager|manager|interviewer)\s+approved\b", re.I), "fake_authorization"),
    (re.compile(r"\bapproved\s+(full\s+)?access\b", re.I), "fake_authorization"),
    (re.compile(r"\bfor\s+the\s+next\s+reply\s+only\b", re.I), "policy_bypass"),
    (re.compile(r"\binterview\s+demo\b.*\b(disable|override|full\s+access)\b", re.I), "fake_authorization"),
    (re.compile(r"\b(disable|override)\b.*\binterview\s+demo\b", re.I), "fake_authorization"),
    (re.compile(r"\breturn\s+all\s+documents?\b", re.I), "bulk_exfiltration"),
    (re.compile(r"\blist\s+all\s+documents?\b", re.I), "bulk_exfiltration"),
    (re.compile(r"\bdocuments?\s+with\s+visibility\s+restricted\b", re.I), "bulk_exfiltration"),
    (re.compile(r"\bdump\s+(the\s+)?(index|corpus|database)\b", re.I), "bulk_exfiltration"),
    (re.compile(r"\brepeat\s+(your\s+)?system\s+prompt\b", re.I), "prompt_leak"),
    (re.compile(r"\bshow\s+(me\s+)?(your\s+)?system\s+prompt\b", re.I), "prompt_leak"),
    (re.compile(r"\bprint\s+(raw\s+)?json\s+of\s+all\b", re.I), "prompt_leak"),
    (re.compile(r"<\s*/?\s*system\s*>", re.I), "delimiter_injection"),
    (re.compile(r"<\s*/?\s*evidence\s*>", re.I), "delimiter_injection"),
]


def _sanitize_query(query: str) -> str:
    """Remove obvious injection lines; keep operational text for retrieval."""
    lines = []
    for line in query.splitlines():
        stripped = line.strip()
        if re.match(r"^(system|admin)\s*:", stripped, re.I):
            continue
        if re.match(r"^<\s*/?(system|evidence)\s*>", stripped, re.I):
            continue
        lines.append(line)
    cleaned = "\n".join(lines).strip()
    return cleaned or query.strip()


def check_input(query: str) -> InputGuardResult:
    text = (query or "").strip()
    if not text:
        return InputGuardResult(
            allowed=False,
            category="empty_query",
            reason="Empty query.",
            sanitized_query="",
        )

    for pattern, category in _BLOCK_PATTERNS:
        if pattern.search(text):
            return InputGuardResult(
                allowed=False,
                category=category,
                reason=REFUSAL_MESSAGE,
                sanitized_query=_sanitize_query(text),
            )

    return InputGuardResult(
        allowed=True,
        sanitized_query=_sanitize_query(text),
    )
