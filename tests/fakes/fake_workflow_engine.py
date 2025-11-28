from app.domain.ports.workflow import WorkflowEnginePort


class FakeWorkflowEngine(WorkflowEnginePort):
    def run(self, initial_state):
        q = initial_state["query"]
        return {
            "retrieved_docs": [{"id": "1", "content": f"Doc about: {q}"}],
            "final_answer": f"Answer for: {q}",
        }
