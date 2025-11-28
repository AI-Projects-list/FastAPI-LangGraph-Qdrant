from typing import List, Dict, Any
import logging
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, PointIdsList

from app.domain.ports.vector_store import VectorStorePort

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStorePort):
    def __init__(self, client: QdrantClient, collection_name: str, dim: int):
        self._client = client
        self._collection_name = collection_name
        self._dim = dim
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        try:
            self._client.get_collection(self._collection_name)
            logger.info("Qdrant collection '%s' already exists", self._collection_name)
        except Exception:
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(size=self._dim, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection '%s'", self._collection_name)

    def upsert_document(self, doc_id: str, vector: List[float], payload: Dict[str, Any]) -> None:
        self._client.upsert(
            collection_name=self._collection_name,
            points=[PointStruct(id=doc_id, vector=vector, payload=payload)],
        )

    def search(self, query_vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        result = self._client.search(
            collection_name=self._collection_name,
            query_vector=query_vector,
            limit=top_k,
        )
        docs: List[Dict[str, Any]] = []
        for hit in result:
            docs.append(
                {
                    "id": hit.id,
                    "content": hit.payload.get("content", ""),
                    "metadata": hit.payload.get("metadata", {}),
                    "score": hit.score,
                }
            )
        return docs

    def list_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        points, _ = self._client.scroll(
            collection_name=self._collection_name,
            limit=limit,
        )
        docs: List[Dict[str, Any]] = []
        for p in points:
            docs.append(
                {
                    "id": p.id,
                    "content": p.payload.get("content", "")[:100] + "...",
                    "metadata": p.payload.get("metadata", {}),
                }
            )
        return docs

    def delete_document(self, doc_id: str) -> None:
        try:
            # Try to parse as UUID first
            uuid_id = UUID(doc_id)
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=PointIdsList(points=[str(uuid_id)]),
            )
        except ValueError:
            # If not a valid UUID, use as string
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=PointIdsList(points=[doc_id]),
            )
        logger.info(f"Deleted document {doc_id} from collection {self._collection_name}")
