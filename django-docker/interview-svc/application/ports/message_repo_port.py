from abc import ABC, abstractmethod
from typing import Any


class MessageRepoPort(ABC):
    @abstractmethod
    def save(
        self, session_id: str, user_sub: str | None, payload: dict[str, Any]
    ) -> None: ...
