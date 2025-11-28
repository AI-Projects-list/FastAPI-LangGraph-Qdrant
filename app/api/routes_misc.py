from fastapi import APIRouter, Depends

from app.api.deps import get_counter_service
from app.application.services.counter_service import CounterService

router = APIRouter(tags=["misc"])


@router.get("/counter")
async def get_counter(counter_service: CounterService = Depends(get_counter_service)):
    value = counter_service.increment()
    return {"counter": value}
