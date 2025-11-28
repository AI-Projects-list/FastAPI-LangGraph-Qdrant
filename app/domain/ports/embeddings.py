from abc import ABC, abstractmethod
from typing import List


class EmbeddingsPort(ABC):
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        ...
