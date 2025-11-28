from abc import ABC, abstractmethod
from typing import Dict, Any


class StateStorePort(ABC):
    @abstractmethod
    def save(self, key: str, value: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def get_all_keys(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def count(self) -> int:
        ...
