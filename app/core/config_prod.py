from .config import Settings


class ProdSettings(Settings):
    environment: str = "prod"
    log_level: str = "WARNING"
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6334
