from abc import ABC, abstractmethod
from typing import List, Dict, Any


class VectorStorePort(ABC):
    @abstractmethod
    def upsert_document(self, doc_id: str, vector: List[float], payload: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def list_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def delete_document(self, doc_id: str) -> None:
        ...
