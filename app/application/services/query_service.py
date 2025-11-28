from typing import Dict, Any
from time import time

from app.domain.ports.workflow import WorkflowEnginePort


class QueryService:
    def __init__(self, workflow_engine: WorkflowEnginePort):
        self._workflow_engine = workflow_engine

    async def run_query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        start = time()
        initial_state = {
            "query": query,
            "top_k": top_k,
            "retrieved_docs": [],
            "final_answer": "",
            "processing_steps": [],
            "error": None,
        }
        final_state = self._workflow_engine.run(initial_state)
        elapsed = time() - start
        return {
            "initial_query": query,
            "retrieved_docs": final_state.get("retrieved_docs", []),
            "final_answer": final_state.get("final_answer", ""),
            "processing_time": elapsed,
        }
