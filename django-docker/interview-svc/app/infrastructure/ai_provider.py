import os
import httpx  # type: ignore
from fastapi import HTTPException  # type: ignore
from app.domain.models import ChatRequest, ChatResponse  # type: ignore
from app.domain.ports import LLMPort  # type: ignore


class HttpLLMAdapter(LLMPort):
    """Adaptador concreto que conecta con un proveedor OpenAI-compatible."""

    def __init__(self):
        self.base_url = os.getenv("PROVIDER_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("PROVIDER_API_KEY", "")
        self.model = os.getenv("PROVIDER_MODEL", "gpt-4o-mini")
        self.timeout = 60.0

        if not self.base_url or not self.api_key:
            raise RuntimeError("LLM provider not configured")

        if not self.model:
            raise RuntimeError("LLM model not configured")

    def chat(self, req: ChatRequest) -> ChatResponse:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Eres un entrevistador amable."},
                {"role": "user", "content": req.message.strip() or "Hola"},
            ],
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()

            choice = (data.get("choices") or [{}])[0]
            content = choice.get("message", {}).get("content", "")
            return ChatResponse(reply=content.strip() or "(sin respuesta)")

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.text
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
