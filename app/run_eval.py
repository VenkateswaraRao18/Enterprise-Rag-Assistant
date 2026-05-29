import argparse
import json

from app.eval.runner import EvalRunner, EVAL_REPORT_JSON, EVAL_REPORT_MD


def main():
    parser = argparse.ArgumentParser(description="Evaluate TechCorp RAG pipeline")
    parser.add_argument(
        "--mode",
        choices=["retrieval", "full"],
        default="retrieval",
        help="retrieval=hybrid only (fast), full=includes Ollama generation",
    )
    parser.add_argument("--ids", type=str, default="", help="Comma-separated case ids, e.g. q21,q22,q25")
    parser.add_argument("--limit", type=int, default=0, help="Run only first N cases")
    parser.add_argument("--top-k", type=int, default=6)
    args = parser.parse_args()

    case_ids = [x.strip() for x in args.ids.split(",") if x.strip()] or None
    limit = args.limit if args.limit > 0 else None

    runner = EvalRunner(mode=args.mode)
    report = runner.run_all(case_ids=case_ids, limit=limit, top_k=args.top_k)
    runner.save_report(report)

    print("\n" + json.dumps(report["summary"], indent=2))
    print(f"\nWrote {EVAL_REPORT_JSON}")
    print(f"Wrote {EVAL_REPORT_MD}")


if __name__ == "__main__":
    main()
