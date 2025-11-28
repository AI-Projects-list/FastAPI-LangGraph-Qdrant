from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class DocumentInput(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None


class QueryInput(BaseModel):
    query: str
    top_k: int = 5


class WorkflowResult(BaseModel):
    initial_query: str
    retrieved_docs: List[Dict[str, Any]]
    final_answer: str
    processing_time: float
