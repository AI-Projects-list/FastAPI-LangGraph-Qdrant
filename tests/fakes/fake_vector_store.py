from app.domain.ports.vector_store import VectorStorePort


class FakeVectorStore(VectorStorePort):
    def __init__(self):
        self.docs = {}

    def upsert_document(self, doc_id, vector, payload):
        self.docs[doc_id] = {"vector": vector, "payload": payload}

    def search(self, query_vector, top_k):
        results = []
        for doc_id, item in self.docs.items():
            results.append({
                "id": doc_id,
                "content": item["payload"]["content"],
                "metadata": item["payload"]["metadata"],
                "score": 1.0,
            })
        return results[:top_k]

    def list_documents(self, limit=10):
        return [
            {
                "id": doc_id,
                "content": item["payload"]["content"],
                "metadata": item["payload"]["metadata"],
            }
            for doc_id, item in list(self.docs.items())[:limit]
        ]

    def delete_document(self, doc_id):
        self.docs.pop(doc_id, None)
