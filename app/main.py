from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.container import build_container, AppContainer
from app.api import routes_documents, routes_query, routes_health, routes_debug, routes_misc


@asynccontextmanager
async def lifespan(app: FastAPI):
    container: AppContainer = build_container()
    app.state.container = container  # type: ignore[attr-defined]
    yield
    container.qdrant_client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Clean LangGraph + Qdrant API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(routes_documents.router)
    app.include_router(routes_query.router)
    app.include_router(routes_health.router)
    app.include_router(routes_debug.router)
    app.include_router(routes_misc.router)
    return app
