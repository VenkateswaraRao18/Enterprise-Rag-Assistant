import json
import uuid
from pathlib import Path

from app.pipeline.idempotency import FingerprintStore
from app.pipeline.loaders import load_incidents, load_jira, load_kb, load_oncall, load_slack
from app.pipeline.report import IngestionReport


def run():
    run_id = str(uuid.uuid4())
    data_dir = Path("synthetic_data/techcorp")
    out_dir = Path("app/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    fp_store = FingerprintStore(out_dir / "fingerprints.json")
    report = IngestionReport()

    ingestion_plan = [
        ("incident", load_incidents, data_dir / "incidents.json"),
        ("jira", load_jira, data_dir / "jira_issues.json"),
        ("kb", load_kb, data_dir / "kb_documents.json"),
        ("slack", load_slack, data_dir / "slack_messages.json"),
        ("oncall", load_oncall, data_dir / "oncall_roster.csv"),
    ]

    all_docs = []
    upsert_docs = []
    for source_name, fn, path in ingestion_plan:
        docs = fn(path, run_id)
        report.read[source_name] += len(docs)

        for d in docs:
            try:
                doc_payload = d.model_dump(mode="json")
                all_docs.append(doc_payload)
                if fp_store.should_upsert(d):
                    upsert_docs.append(doc_payload)
                    report.upserted[source_name] += 1
                else:
                    report.skipped[source_name] += 1
            except Exception:
                report.failed[source_name] += 1

    fp_store.save()

    (out_dir / "canonical_docs.json").write_text(json.dumps(all_docs, indent=2), encoding="utf-8")
    (out_dir / "upsert_docs.json").write_text(json.dumps(upsert_docs, indent=2), encoding="utf-8")
    (out_dir / "ingestion_report.json").write_text(json.dumps(report.as_dict(), indent=2), encoding="utf-8")

    print(f"Run ID: {run_id}")
    print(json.dumps(report.as_dict(), indent=2))


if __name__ == "__main__":
    run()
