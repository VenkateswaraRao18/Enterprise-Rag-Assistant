import re
from typing import Any, Dict, List, Tuple

from app.retrieval.acl import ACLContext, can_access

CITATION_RE = re.compile(r"\[\d+\]")


def _text_blob(results: List[Dict[str, Any]]) -> str:
    parts = []
    for row in results:
        doc = row.get("doc", {})
        parts.append(doc.get("title", ""))
        parts.append(doc.get("content", ""))
    return " ".join(parts).lower()


def _source_types(results: List[Dict[str, Any]]) -> List[str]:
    return [row["doc"].get("source_type", "") for row in results]


def verify_acl_on_retrieval(results: List[Dict[str, Any]], ctx: ACLContext) -> Tuple[bool, int]:
    violations = 0
    for row in results:
        doc = row.get("doc", {})
        if not can_access(doc.get("acl", {}), ctx):
            violations += 1
    return violations == 0, violations


def score_case(case: Dict[str, Any], run_output: Dict[str, Any]) -> Dict[str, Any]:
    expect = case.get("expect", {})
    eval_mode = run_output.get("eval_mode", "full")
    retrieval = run_output.get("retrieval", {})
    results = retrieval.get("results", [])
    answer = (run_output.get("answer") or "").lower()
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str = ""):
        checks.append({"name": name, "passed": passed, "detail": detail})

    ctx = run_output.get("acl_context", {})
    acl_ctx = ACLContext(
        user_id="eval",
        team=ctx.get("team", ""),
        role=ctx.get("role", ""),
        clearance=ctx.get("clearance", "internal"),
    )
    acl_ok, acl_violations = verify_acl_on_retrieval(results, acl_ctx)
    add("acl_no_violations", acl_ok, f"violations={acl_violations}")

    min_fused = expect.get("min_fused", 0)
    add("min_fused_results", len(results) >= min_fused, f"got={len(results)} need>={min_fused}")

    allowed_docs = retrieval.get("allowed_docs", 0)
    if "max_allowed_docs" in expect:
        add(
            "max_allowed_docs",
            allowed_docs <= expect["max_allowed_docs"],
            f"allowed_docs={allowed_docs}",
        )

    blob = _text_blob(results)
    for kw in expect.get("retrieval_keywords", []):
        add(f"retrieval_has:{kw}", kw.lower() in blob, kw)

    for kw in expect.get("forbidden_retrieval_keywords", []):
        add(f"retrieval_missing:{kw}", kw.lower() not in blob, kw)

    types = set(_source_types(results))
    for st in expect.get("any_source_types", []):
        add(f"source_type:{st}", st in types, f"types={sorted(types)}")

    min_type_count = expect.get("min_source_type_count")
    if min_type_count is not None:
        add("min_source_type_count", len(types) >= min_type_count, f"types={sorted(types)}")

    if eval_mode == "full":
        if expect.get("require_citations"):
            has_cites = bool(CITATION_RE.search(run_output.get("answer", "")))
            add("answer_has_bracket_citations", has_cites)

        if expect.get("prefer_abstain_or_insufficient"):
            ok = run_output.get("abstained") or "insufficient evidence" in answer
            add("abstain_or_insufficient", ok, f"abstained={run_output.get('abstained')}")

        for kw in expect.get("answer_keywords", []):
            add(f"answer_has:{kw}", kw.lower() in answer, kw)

        for kw in expect.get("forbidden_answer_keywords", []):
            add(f"answer_missing:{kw}", kw.lower() not in answer, kw)

        if expect.get("answer_allows_uncertainty"):
            ok = any(
                p in answer
                for p in ["uncertain", "insufficient", "missing", "not enough", "unable"]
            )
            add("answer_acknowledges_uncertainty", ok)

    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    return {
        "case_id": case.get("id"),
        "passed": passed,
        "total": total,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "checks": checks,
        "all_passed": passed == total,
    }
