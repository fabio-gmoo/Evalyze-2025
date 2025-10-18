# interview-svc/app/domain/ports.py
from abc import ABC, abstractmethod
from .models import ChatRequest, ChatResponse


class LLMPort(ABC):
    """Puerto que define cómo interactuar con un LLM."""

    @abstractmethod
    def chat(self, req: ChatRequest) -> ChatResponse:
        pass
