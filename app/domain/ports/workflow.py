from abc import ABC, abstractmethod
from typing import Dict, Any


class WorkflowEnginePort(ABC):
    @abstractmethod
    def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        ...
