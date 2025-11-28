from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.core.container import AppContainer

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(container: AppContainer = Depends(get_container)):
    qdrant_healthy = False
    try:
        container.qdrant_client.get_collection(container.settings.qdrant_collection_name)
        qdrant_healthy = True
    except Exception:
        qdrant_healthy = False

    return {
        "status": "healthy" if qdrant_healthy and container.workflow_engine else "unhealthy",
        "qdrant": "connected" if qdrant_healthy else "disconnected",
        "workflow": "ready" if container.workflow_engine else "not ready",
        "documents_in_memory": container.state_store.count(),
    }
