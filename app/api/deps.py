from fastapi import Depends, Request

from app.core.container import AppContainer
from app.application.services.document_service import DocumentService
from app.application.services.query_service import QueryService
from app.application.services.counter_service import CounterService


def get_container(request: Request) -> AppContainer:
    return request.app.state.container  # type: ignore[attr-defined]


def get_document_service(container: AppContainer = Depends(get_container)) -> DocumentService:
    return container.document_service


def get_query_service(container: AppContainer = Depends(get_container)) -> QueryService:
    return container.query_service


def get_counter_service(container: AppContainer = Depends(get_container)) -> CounterService:
    return container.counter_service
