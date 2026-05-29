import json
from pathlib import Path

from app.utils.helpers import normalize_text, stable_hash


class FingerprintStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = {}
        if path.exists():
            self.data = json.loads(path.read_text(encoding="utf-8"))

    def fingerprint(self, doc):
        base = f"{doc.source_type}|{doc.source_id}|{doc.updated_at.isoformat()}|{stable_hash(normalize_text(doc.content))}"
        return stable_hash(base)

    def should_upsert(self, doc):
        key = f"{doc.source_type}:{doc.source_id}"
        fp = self.fingerprint(doc)
        old = self.data.get(key)
        if old == fp:
            return False
        self.data[key] = fp
        return True

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
