import random
from datetime import datetime
import asyncio

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.core.container import AppContainer

router = APIRouter(tags=["debug"])


@router.get("/debug/state")
async def debug_state(container: AppContainer = Depends(get_container)):
    return {
        "state_store_keys": list(container.state_store.get_all_keys().keys()),
        "collection_name": container.settings.qdrant_collection_name,
        "embedding_dim": container.settings.embedding_dim,
    }


@router.get("/chaos")
async def chaos_mode():
    await asyncio.sleep(random.uniform(0.1, 2.0))
    return {
        "message": "Chaos mode activated!",
        "random_number": random.randint(1, 100),
        "timestamp": datetime.utcnow().isoformat(),
    }
