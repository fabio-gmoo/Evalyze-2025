# ai_router.py
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
import os
import httpx

router = APIRouter(prefix="/ai", tags=["ai"])

# === Config obligatoria por variables de entorno ===
# Ejemplos:
#   PROVIDER_BASE_URL=https://api.openai.com
#   PROVIDER_BASE_URL=https://openrouter.ai/api
#   PROVIDER_BASE_URL=https://api.together.xyz
#   PROVIDER_BASE_URL=https://api.groq.com/openai
PROVIDER_BASE_URL = os.getenv("PROVIDER_BASE_URL", "").rstrip("/")
PROVIDER_API_KEY = os.getenv("PROVIDER_API_KEY", "")
# pon aquí tu modelo real
PROVIDER_MODEL = os.getenv("PROVIDER_MODEL", "gpt-4o-mini")
# opcional: API key propia para tu endpoint
PUBLIC_API_KEY = os.getenv("AI_PUBLIC_API_KEY", "")


def _require_config():
    if not PROVIDER_BASE_URL or not PROVIDER_API_KEY or not PROVIDER_MODEL:
        raise HTTPException(
            status_code=500,
            detail="AI provider not configured. Set PROVIDER_BASE_URL, PROVIDER_API_KEY, PROVIDER_MODEL.",
        )


def _check_public_key(x_api_key: str | None):
    if not PUBLIC_API_KEY:
        return
    if x_api_key != PUBLIC_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.get("/health")
def health():
    # No exponemos el API key en salud
    return {
        "status": "ok",
        "provider_base": bool(PROVIDER_BASE_URL),
        "model": PROVIDER_MODEL if PROVIDER_MODEL else None,
    }


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, x_api_key: str | None = Header(default=None)):
    _check_public_key(x_api_key)
    _require_config()

    url = f"{PROVIDER_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {PROVIDER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": PROVIDER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Eres un entrevistador amable y profesional.",
            },
            {"role": "user", "content": (req.message or "").strip() or "Hola"},
        ],
        "temperature": 0.7,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            # OpenAI-compatible → respuesta en choices[0].message.content
            text = (
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            ) or "(sin respuesta)"
            return {"reply": text.strip()}
    except httpx.HTTPStatusError as e:
        # Propaga el status del proveedor para facilitar debug
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
