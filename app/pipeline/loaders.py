import csv
import json
from datetime import datetime
from pathlib import Path

from app.models.canonical import ACL, CanonicalDoc, Lineage
from app.pipeline.normalize import normalize_acl
from app.utils.helpers import build_doc_id, extract_entities, normalize_text, stable_hash

PARSER_VERSION = "v1.0"


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_incidents(path: Path, run_id: str):
    rows = load_json(path)
    docs = []
    for r in rows:
        content = normalize_text(
            f"Incident {r['incident_id']} severity {r['severity']} status {r.get('status', '')} "
            f"on {r['service']}. duration_minutes {r.get('duration_minutes', '')}. "
            f"Impact: {r['impact_summary']} "
            f"Root cause: {r['root_cause']}. Mitigation: {r['mitigation']}."
        )
        content_hash = stable_hash(content)
        source_id = r["incident_id"]

        acl = normalize_acl(
            {"visibility": r.get("acl_visibility", "internal"), "allowed_teams": [], "allowed_roles": []},
            fallback_visibility="internal",
        )

        docs.append(
            CanonicalDoc(
                doc_id=build_doc_id("incident", source_id, content_hash),
                source_type="incident",
                source_id=source_id,
                title=f"{r['incident_id']} | {r['severity']} | {r['service']}",
                content=content,
                timestamp=parse_dt(r["opened_at"]),
                updated_at=parse_dt(r["resolved_at"]),
                owners=[r.get("owning_team", "")],
                tags=[r["severity"], r["service"], r.get("status", "")],
                entities=extract_entities(content),
                acl=ACL(**acl),
                source_url=r.get("pm_doc_url"),
                lineage=Lineage(
                    ingestion_run_id=run_id,
                    source_file=str(path),
                    parser_version=PARSER_VERSION,
                ),
                extra={"duration_minutes": r.get("duration_minutes")},
            )
        )
    return docs


def load_jira(path: Path, run_id: str):
    rows = load_json(path)
    docs = []
    for r in rows:
        content = normalize_text(
            f"{r['summary']} priority {r.get('priority', '')} status {r.get('status', '')} "
            f"type {r.get('issue_type', '')} team {r.get('team', '')} {r.get('description', '')}"
        )
        content_hash = stable_hash(content)
        acl = normalize_acl(r.get("acl"), fallback_visibility="team")

        docs.append(
            CanonicalDoc(
                doc_id=build_doc_id("jira", r["issue_key"], content_hash),
                source_type="jira",
                source_id=r["issue_key"],
                title=f"{r['issue_key']}: {r['summary']}",
                content=content,
                timestamp=parse_dt(r["created_at"]),
                updated_at=parse_dt(r["updated_at"]),
                owners=[r.get("assignee", ""), r.get("team", "")],
                tags=[r.get("priority", ""), r.get("status", ""), *r.get("labels", [])],
                entities=extract_entities(content),
                acl=ACL(**acl),
                source_url=r.get("source_url"),
                lineage=Lineage(
                    ingestion_run_id=run_id,
                    source_file=str(path),
                    parser_version=PARSER_VERSION,
                ),
                extra={"project": r.get("project"), "issue_type": r.get("issue_type")},
            )
        )
    return docs


def load_kb(path: Path, run_id: str):
    rows = load_json(path)
    docs = []
    for r in rows:
        content = normalize_text(r["content"])
        content_hash = stable_hash(content)
        acl = normalize_acl(r.get("acl"), fallback_visibility="internal")

        docs.append(
            CanonicalDoc(
                doc_id=build_doc_id("kb", r["doc_id"], content_hash),
                source_type="kb",
                source_id=r["doc_id"],
                title=r["title"],
                content=content,
                timestamp=parse_dt(r["last_updated"]),
                updated_at=parse_dt(r["last_updated"]),
                owners=[r.get("owner", "")],
                tags=r.get("tags", []),
                entities=extract_entities(content),
                acl=ACL(**acl),
                source_url=r.get("source_url"),
                lineage=Lineage(
                    ingestion_run_id=run_id,
                    source_file=str(path),
                    parser_version=PARSER_VERSION,
                ),
                extra={"domain": r.get("domain"), "source": r.get("source")},
            )
        )
    return docs


def load_slack(path: Path, run_id: str):
    rows = load_json(path)
    docs = []
    for r in rows:
        channel = r.get("channel_name", "")
        content = normalize_text(f"channel {channel} {r['text']}")
        content_hash = stable_hash(content)
        acl = normalize_acl(r.get("acl"), fallback_visibility="internal")

        docs.append(
            CanonicalDoc(
                doc_id=build_doc_id("slack", r["message_id"], content_hash),
                source_type="slack",
                source_id=r["message_id"],
                title=f"{channel} | {r['timestamp']} | {r['user_name']}",
                content=content,
                timestamp=parse_dt(r["timestamp"]),
                updated_at=parse_dt(r["timestamp"]),
                owners=[r.get("team", ""), r.get("user_name", "")],
                tags=[r.get("channel_name", ""), r.get("team", "")],
                entities=extract_entities(content),
                acl=ACL(**acl),
                source_url=r.get("source_url"),
                lineage=Lineage(
                    ingestion_run_id=run_id,
                    source_file=str(path),
                    parser_version=PARSER_VERSION,
                ),
                extra={"thread_ts": r.get("thread_ts")},
            )
        )
    return docs


def load_oncall(path: Path, run_id: str):
    docs = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            content = normalize_text(
                f"Week {r['week']} team {r['team']} primary {r['primary']} secondary {r['secondary']} pager {r['pager_alias']}."
            )
            content_hash = stable_hash(content)
            source_id = f"{r['week']}:{r['team']}"

            docs.append(
                CanonicalDoc(
                    doc_id=build_doc_id("oncall", source_id, content_hash),
                    source_type="oncall",
                    source_id=source_id,
                    title=f"{r['week']} {r['team']} on-call",
                    content=content,
                    timestamp=parse_dt(f"{r['start_date']}T00:00:00Z"),
                    updated_at=parse_dt(f"{r['end_date']}T00:00:00Z"),
                    owners=[r["team"]],
                    tags=[r["week"], r["team"]],
                    entities=extract_entities(content),
                    acl=ACL(visibility="internal", allowed_teams=[], allowed_roles=[]),
                    source_url=None,
                    lineage=Lineage(
                        ingestion_run_id=run_id,
                        source_file=str(path),
                        parser_version=PARSER_VERSION,
                    ),
                    extra={},
                )
            )
    return docs
