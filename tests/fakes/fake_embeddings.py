from typing import List
from app.domain.ports.embeddings import EmbeddingsPort


class FakeEmbeddings(EmbeddingsPort):
    def embed(self, text: str) -> List[float]:
        return [float(len(text)), float(len(text) * 2)]
