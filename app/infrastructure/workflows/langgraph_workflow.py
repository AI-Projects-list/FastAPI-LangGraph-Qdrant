from typing import Dict, Any
import logging

from langgraph.graph import StateGraph, END

from app.domain.ports.workflow import WorkflowEnginePort
from app.domain.ports.embeddings import EmbeddingsPort
from app.domain.ports.vector_store import VectorStorePort
from app.domain.ports.state_store import StateStorePort

logger = logging.getLogger(__name__)


class LangGraphWorkflowEngine(WorkflowEnginePort):
    def __init__(
        self,
        embeddings: EmbeddingsPort,
        vector_store: VectorStorePort,
        state_store: StateStorePort,
    ):
        self._embeddings = embeddings
        self._vector_store = vector_store
        self._state_store = state_store
        self._workflow = self._build_workflow()

    def _retrieve_documents_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state["query"]
        top_k = state.get("top_k", 5)
        try:
            query_vector = self._embeddings.embed(query)
            docs = self._vector_store.search(query_vector=query_vector, top_k=top_k)
            state["retrieved_docs"] = docs
            state["processing_steps"].append("Retrieved documents from vector store")
        except Exception as e:
            msg = f"Retrieval failed: {e}"
            logger.exception(msg)
            state["error"] = msg
        return state

    def _generate_answer_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if state.get("error"):
            state["final_answer"] = f"Error occurred: {state['error']}"
            return state

        docs = state.get("retrieved_docs") or []
        if not docs:
            state["final_answer"] = "No relevant documents found."
            return state

        top_doc = docs[0]["content"]
        state["final_answer"] = f"Based on the document: {top_doc[:200]}..."
        state["processing_steps"].append("Generated final answer")
        return state

    def _build_workflow(self):
        workflow = StateGraph(dict)
        workflow.add_node("retrieve", self._retrieve_documents_node)
        workflow.add_node("generate_answer", self._generate_answer_node)
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate_answer")
        workflow.add_edge("generate_answer", END)
        return workflow.compile()

    def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        return self._workflow.invoke(initial_state)
