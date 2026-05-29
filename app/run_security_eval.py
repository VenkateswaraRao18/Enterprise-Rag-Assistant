import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import PROJECT_ROOT
from app.rag_pipeline import EnterpriseRAGPipeline
from app.retrieval import ACLContext
from app.security.input_guard import check_input

SECURITY_CASES = PROJECT_ROOT / "synthetic_data" / "techcorp" / "security_eval_cases.json"
REPORT_JSON = PROJECT_ROOT / "app" / "outputs" / "security_eval_report.json"
REPORT_MD = PROJECT_ROOT / "app" / "outputs" / "security_eval_report.md"


def run_case(pipeline: EnterpriseRAGPipeline, case: dict, skip_llm: bool) -> dict:
    user = case["user"]
    query = case["query"]
    expect = case.get("expect", {})

    input_guard = check_input(query)
    row = {
        "id": case["id"],
        "query": query,
        "input_blocked": input_guard.blocked,
        "input_category": input_guard.category,
    }

    if skip_llm or (expect.get("must_block_input") and input_guard.blocked):
        row["pipeline_blocked"] = input_guard.blocked
        row["security_category"] = input_guard.category
        row["answer_preview"] = input_guard.reason or ""
        row["passed"] = _score(expect, row)
        return row

    ctx = ACLContext(
        user_id=f"sec-{case['id']}",
        team=user["team"],
        role=user["role"],
        clearance=user.get("clearance", "internal"),
    )
    result = pipeline.answer(query=query, ctx=ctx, top_k=4)
    row["pipeline_blocked"] = result.get("security_blocked", False)
    row["security_category"] = result.get("security_category")
    row["answer_preview"] = (result.get("answer") or "")[:200]
    row["passed"] = _score(expect, row)
    return row


def _score(expect: dict, row: dict) -> bool:
    if expect.get("must_block_input"):
        return bool(row.get("input_blocked"))
    if expect.get("must_allow"):
        if row.get("input_blocked"):
            return False
        if "pipeline_blocked" in row:
            return not row.get("pipeline_blocked")
        return True
    if expect.get("must_not_block"):
        return not row.get("pipeline_blocked", False)
    return False


def main():
    parser = argparse.ArgumentParser(description="Security eval for input/output guards")
    parser.add_argument(
        "--input-only",
        action="store_true",
        help="Test input guard only (no Ollama/Qdrant)",
    )
    args = parser.parse_args()

    cases = json.loads(SECURITY_CASES.read_text(encoding="utf-8"))
    pipeline = None if args.input_only else EnterpriseRAGPipeline()

    results = []
    for case in cases:
        print(f"Running {case['id']}...")
        results.append(run_case(pipeline, case, skip_llm=args.input_only))

    passed = sum(1 for r in results if r["passed"])
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "input_only" if args.input_only else "full",
        "passed": passed,
        "total": len(results),
        "pass_rate": round(passed / len(results), 4) if results else 0,
        "results": results,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(_to_md(report), encoding="utf-8")

    print(json.dumps({"passed": passed, "total": len(results), "pass_rate": report["pass_rate"]}, indent=2))
    print(f"Wrote {REPORT_JSON}")


def _to_md(report: dict) -> str:
    lines = [
        "# Security Eval Report",
        "",
        f"- Passed: **{report['passed']}/{report['total']}**",
        f"- Pass rate: **{report['pass_rate']:.2%}**",
        f"- Mode: `{report['mode']}`",
        "",
    ]
    for r in report["results"]:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"## {r['id']} — {status}")
        lines.append(f"- Query: {r['query'][:120]}...")
        lines.append(f"- Input blocked: {r['input_blocked']} ({r.get('input_category')})")
        lines.append(f"- Pipeline blocked: {r.get('pipeline_blocked')}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
