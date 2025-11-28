from .config import Settings


class StagingSettings(Settings):
    environment: str = "staging"
    log_level: str = "INFO"
    qdrant_host: str = "staging-qdrant-service"
    qdrant_port: int = 6334
