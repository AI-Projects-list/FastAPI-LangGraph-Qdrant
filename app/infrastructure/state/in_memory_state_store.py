from typing import Dict, Any
import threading

from app.domain.ports.state_store import StateStorePort


class InMemoryStateStore(StateStorePort):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[str, Dict[str, Any]] = {}

    def save(self, key: str, value: Dict[str, Any]) -> None:
        with self._lock:
            self._store[key] = value

    def get_all_keys(self) -> Dict[str, Any]:
        with self._lock:
            return {k: v for k, v in self._store.items()}

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def count(self) -> int:
        with self._lock:
            return len(self._store)
