from abc import ABC, abstractmethod


class AiLlmPort(ABC):
    @abstractmethod
    def chat(self, system_prompt: str, user_message: str) -> str: ...
