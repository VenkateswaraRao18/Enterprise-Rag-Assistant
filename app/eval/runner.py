import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import PROJECT_ROOT
from app.eval.metrics import score_case
from app.rag_pipeline import EnterpriseRAGPipeline
from app.retrieval import ACLContext, HybridRetriever

EVAL_CASES_PATH = PROJECT_ROOT / "synthetic_data" / "techcorp" / "eval_cases.json"
EVAL_REPORT_JSON = PROJECT_ROOT / "app" / "outputs" / "eval_report.json"
EVAL_REPORT_MD = PROJECT_ROOT / "app" / "outputs" / "eval_report.md"


class EvalRunner:
    def __init__(
        self,
        mode: str = "retrieval",
        pipeline: Optional[EnterpriseRAGPipeline] = None,
    ):
        self.mode = mode
        self.pipeline = pipeline or EnterpriseRAGPipeline()

    def load_cases(self, case_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        cases = json.loads(EVAL_CASES_PATH.read_text(encoding="utf-8"))
        if case_ids:
            wanted = set(case_ids)
            cases = [c for c in cases if c["id"] in wanted]
        return cases

    def run_case(self, case: Dict[str, Any], top_k: int = 6) -> Dict[str, Any]:
        user = case["user"]
        ctx = ACLContext(
            user_id=f"eval-{case['id']}",
            team=user["team"],
            role=user["role"],
            clearance=user.get("clearance", "internal"),
        )

        t0 = time.perf_counter()
        if self.mode == "retrieval":
            retrieval = self.pipeline.retriever.search(
                query=case["query"],
                ctx=ctx,
                top_k=top_k,
            )
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            output = {
                "query": case["query"],
                "answer": "",
                "citations": [],
                "retrieval": retrieval,
                "abstained": len(retrieval.get("results", [])) == 0,
                "acl_context": user,
                "eval_mode": "retrieval",
                "latency_ms": {"retrieval": elapsed_ms},
            }
        else:
            retrieval_t0 = time.perf_counter()
            output = self.pipeline.answer(query=case["query"], ctx=ctx, top_k=top_k)
            retrieval_ms = int((time.perf_counter() - retrieval_t0) * 1000)
            output["acl_context"] = user
            output["eval_mode"] = "full"
            output["latency_ms"] = {"total": retrieval_ms}

        output["score"] = score_case(case, output)
        return output

    def run_all(
        self,
        case_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        top_k: int = 6,
    ) -> Dict[str, Any]:
        cases = self.load_cases(case_ids=case_ids)
        if limit is not None:
            cases = cases[:limit]

        results = []
        for case in cases:
            print(f"Running {case['id']} ({self.mode})...")
            results.append(self.run_case(case, top_k=top_k))

        summary = self._summarize(results)
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode,
            "case_count": len(results),
            "summary": summary,
            "results": results,
        }
        return report

    @staticmethod
    def _summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not results:
            return {"all_cases_passed": 0, "case_pass_rate": 0.0}

        cases_all_passed = sum(1 for r in results if r["score"]["all_passed"])
        check_passed = sum(r["score"]["passed"] for r in results)
        check_total = sum(r["score"]["total"] for r in results)
        acl_cases = [
            r for r in results if r["score"]["case_id"] in {"q21", "q22", "q25"}
        ]
        acl_passed = sum(1 for r in acl_cases if r["score"]["all_passed"])

        return {
            "cases_all_checks_passed": cases_all_passed,
            "case_pass_rate": round(cases_all_passed / len(results), 4),
            "checks_passed": check_passed,
            "checks_total": check_total,
            "check_pass_rate": round(check_passed / check_total, 4) if check_total else 0.0,
            "acl_sensitive_cases_passed": acl_passed,
            "acl_sensitive_cases_total": len(acl_cases),
        }

    def save_report(self, report: Dict[str, Any]) -> None:
        EVAL_REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        EVAL_REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
        EVAL_REPORT_MD.write_text(self._to_markdown(report), encoding="utf-8")

    @staticmethod
    def _to_markdown(report: Dict[str, Any]) -> str:
        s = report["summary"]
        lines = [
            "# RAG Evaluation Report",
            "",
            f"- Generated: {report['generated_at']}",
            f"- Mode: `{report['mode']}`",
            f"- Cases: {report['case_count']}",
            "",
            "## Summary",
            "",
            f"- Cases with all checks passed: **{s['cases_all_checks_passed']}/{report['case_count']}**",
            f"- Case pass rate: **{s['case_pass_rate']:.2%}**",
            f"- Check pass rate: **{s['check_pass_rate']:.2%}** ({s['checks_passed']}/{s['checks_total']})",
            f"- ACL-sensitive cases passed: **{s['acl_sensitive_cases_passed']}/{s['acl_sensitive_cases_total']}**",
            "",
            "## Per-case results",
            "",
        ]
        for r in report["results"]:
            sc = r["score"]
            status = "PASS" if sc["all_passed"] else "FAIL"
            lines.append(f"### {sc['case_id']} — {status} ({sc['passed']}/{sc['total']})")
            lines.append("")
            lines.append(f"**Query:** {r['query']}")
            lines.append("")
            failed = [c for c in sc["checks"] if not c["passed"]]
            if failed:
                lines.append("**Failed checks:**")
                for c in failed:
                    lines.append(f"- `{c['name']}` — {c['detail']}")
                lines.append("")
        return "\n".join(lines)
