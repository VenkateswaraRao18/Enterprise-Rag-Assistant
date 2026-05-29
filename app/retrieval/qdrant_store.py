import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    PointStruct,
    VectorParams,
)

from app.config import QDRANT_COLLECTION, QDRANT_URL


def doc_id_to_point_id(doc_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))


def doc_to_payload(doc: Dict[str, Any]) -> Dict[str, Any]:
    acl = doc.get("acl") or {}
    return {
        "doc_id": doc["doc_id"],
        "source_type": doc.get("source_type", ""),
        "source_id": doc.get("source_id", ""),
        "title": doc.get("title", ""),
        "content": doc.get("content", ""),
        "source_url": doc.get("source_url"),
        "timestamp": doc.get("timestamp", ""),
        "updated_at": doc.get("updated_at", ""),
        "tags": doc.get("tags", []) or [],
        "entities": doc.get("entities", []) or [],
        "visibility": acl.get("visibility", "internal"),
        "allowed_teams": acl.get("allowed_teams", []) or [],
        "allowed_roles": acl.get("allowed_roles", []) or [],
    }


class QdrantVectorStore:
    def __init__(
        self,
        url: str = QDRANT_URL,
        collection_name: str = QDRANT_COLLECTION,
    ):
        self.client = QdrantClient(url=url, check_compatibility=False)
        self.collection_name = collection_name

    def collection_exists(self) -> bool:
        try:
            self.client.get_collection(self.collection_name)
            return True
        except Exception:
            return False

    def ensure_collection(self, vector_size: int, recreate: bool = False) -> None:
        if recreate and self.collection_exists():
            self.client.delete_collection(self.collection_name)

        if not self.collection_exists():
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def upsert_points(self, docs: List[Dict[str, Any]], vectors: List[List[float]]) -> int:
        if len(docs) != len(vectors):
            raise ValueError("docs and vectors length mismatch")

        points = []
        for doc, vector in zip(docs, vectors):
            points.append(
                PointStruct(
                    id=doc_id_to_point_id(doc["doc_id"]),
                    vector=vector,
                    payload=doc_to_payload(doc),
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points)
        return len(points)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        allowed_doc_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        query_filter = None
        if allowed_doc_ids is not None:
            if not allowed_doc_ids:
                return []
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchAny(any=allowed_doc_ids),
                    )
                ]
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        hits = response.points or []

        results = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                {
                    "score": float(hit.score),
                    "doc": {
                        "doc_id": payload.get("doc_id"),
                        "source_type": payload.get("source_type"),
                        "source_id": payload.get("source_id"),
                        "title": payload.get("title"),
                        "content": payload.get("content"),
                        "source_url": payload.get("source_url"),
                        "timestamp": payload.get("timestamp"),
                        "updated_at": payload.get("updated_at"),
                        "tags": payload.get("tags", []),
                        "entities": payload.get("entities", []),
                        "acl": {
                            "visibility": payload.get("visibility", "internal"),
                            "allowed_teams": payload.get("allowed_teams", []),
                            "allowed_roles": payload.get("allowed_roles", []),
                        },
                    },
                }
            )
        return results

    def count_points(self) -> int:
        info = self.client.get_collection(self.collection_name)
        return int(info.points_count or 0)
