import math
import re
from collections import Counter
from typing import Any, Dict, Iterable, List

TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-]+")


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [t.lower() for t in TOKEN_RE.findall(text)]


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Dict[str, Any]] = []
        self.doc_tokens: List[List[str]] = []
        self.doc_tf: List[Counter] = []
        self.doc_lens: List[int] = []
        self.avgdl = 0.0
        self.df: Counter = Counter()
        self.idf: Dict[str, float] = {}

    @staticmethod
    def _doc_text(doc: Dict[str, Any]) -> str:
        extra = doc.get("extra") or {}
        extra_txt = " ".join(str(v) for v in extra.values() if v)
        parts = [
            doc.get("title", ""),
            doc.get("content", ""),
            " ".join(doc.get("tags", [])),
            " ".join(doc.get("entities", [])),
            doc.get("source_type", ""),
            extra_txt,
        ]
        return " ".join([p for p in parts if p])

    def fit(self, docs: Iterable[Dict[str, Any]]) -> None:
        self.documents = list(docs)
        self.doc_tokens = []
        self.doc_tf = []
        self.doc_lens = []
        self.df = Counter()
        self.idf = {}

        for doc in self.documents:
            tokens = tokenize(self._doc_text(doc))
            tf = Counter(tokens)
            self.doc_tokens.append(tokens)
            self.doc_tf.append(tf)
            self.doc_lens.append(len(tokens))
            for term in tf:
                self.df[term] += 1

        n_docs = len(self.documents)
        self.avgdl = (sum(self.doc_lens) / n_docs) if n_docs else 0.0
        for term, freq in self.df.items():
            self.idf[term] = math.log(1 + (n_docs - freq + 0.5) / (freq + 0.5))

    def _score_doc(self, query_terms: List[str], idx: int) -> float:
        score = 0.0
        dl = self.doc_lens[idx] if self.doc_lens else 0
        tf = self.doc_tf[idx]

        for term in query_terms:
            if term not in tf:
                continue
            term_idf = self.idf.get(term, 0.0)
            term_freq = tf[term]
            denom = term_freq + self.k1 * (1 - self.b + self.b * (dl / (self.avgdl or 1.0)))
            score += term_idf * ((term_freq * (self.k1 + 1)) / (denom or 1.0))
        return score

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        query_terms = tokenize(query)
        scored = []
        for i, doc in enumerate(self.documents):
            s = self._score_doc(query_terms, i)
            if s > 0:
                scored.append((s, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, doc in scored[:top_k]:
            out.append({"score": round(score, 6), "doc": doc})
        return out
