# interview-svc/app/domain/services.py
from .models import ChatRequest, ChatResponse
from .ports import LLMPort  # type: ignore


class ChatService:
    """Caso de uso principal para manejar el chat."""

    def __init__(self, llm: LLMPort):
        self.llm = llm

    def handle_chat(self, req: ChatRequest) -> ChatResponse:
        return self.llm.chat(req)
