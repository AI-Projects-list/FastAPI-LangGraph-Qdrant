import random
from typing import List

from app.domain.ports.embeddings import EmbeddingsPort


class RandomEmbeddingsService(EmbeddingsPort):
    def __init__(self, dim: int):
        self._dim = dim

    def embed(self, text: str) -> List[float]:
        random.seed(hash(text) % (10**9))
        return [random.random() for _ in range(self._dim)]
