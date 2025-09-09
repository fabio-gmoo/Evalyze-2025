import httpx  # type: ignore
from application.ports.ai_llm_port import AiLlmPort
from infrastructure.config.settings import settings


class OpenAiCompatClient(AiLlmPort):
    def __init__(self) -> None:
        self.base = settings.provider_base_url.rstrip("/")
        self.key = settings.provider_api_key
        self.model = settings.provider_model

    def chat(self, system_prompt: str, user_message: str) -> str:
        url = f"{self.base}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message.strip() or "Hola"},
            ],
            "temperature": 0.7,
            "stream": False,
        }
        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            return (
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            ).strip() or "(sin respuesta)"
