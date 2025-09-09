from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Message:
    session_id: str
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime
