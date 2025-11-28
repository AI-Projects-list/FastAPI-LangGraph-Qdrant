from fastapi import APIRouter, HTTPException, Depends

from app.api.schemas import QueryInput, WorkflowResult
from app.application.services.query_service import QueryService
from app.api.deps import get_query_service

router = APIRouter(tags=["query"])


@router.post("/query", response_model=WorkflowResult)
async def query_documents(
    query_input: QueryInput,
    query_service: QueryService = Depends(get_query_service),
):
    try:
        result = await query_service.run_query(
            query=query_input.query,
            top_k=query_input.top_k,
        )
        return WorkflowResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {e}")
