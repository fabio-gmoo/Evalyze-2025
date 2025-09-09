from abc import ABC, abstractmethod
from typing import Any


class AuthPort(ABC):
    @abstractmethod
    def verify(self, authorization_header: str | None) -> dict[str, Any]: ...
