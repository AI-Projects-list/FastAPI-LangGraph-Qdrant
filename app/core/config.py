from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Clean LangGraph + Qdrant API"
    app_version: str = "1.0.0"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6334
    qdrant_collection_name: str = "documents"

    embedding_dim: int = 384

    environment: str = "local"  # local | dev | staging | prod
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
