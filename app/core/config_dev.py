from .config import Settings


class DevSettings(Settings):
    environment: str = "dev"
    log_level: str = "DEBUG"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6334
