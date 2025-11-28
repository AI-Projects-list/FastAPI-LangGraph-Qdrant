from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]
    ingested_at: datetime
