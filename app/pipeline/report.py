from collections import defaultdict


class IngestionReport:
    def __init__(self):
        self.read = defaultdict(int)
        self.upserted = defaultdict(int)
        self.skipped = defaultdict(int)
        self.failed = defaultdict(int)

    def as_dict(self):
        return {
            "read": dict(self.read),
            "upserted": dict(self.upserted),
            "skipped": dict(self.skipped),
            "failed": dict(self.failed),
        }
