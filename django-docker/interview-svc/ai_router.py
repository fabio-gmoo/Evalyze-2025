# ai_router.py
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
import os
import httpx

router = APIRouter(prefix="/ai", tags=["ai"])
PROVIDER_BASE_URL = os.getenv("PROVIDER_BASE_URL", "").rstrip("/")
PROVIDER_API_KEY = os.getenv("PROVIDER_API_KEY", "")
PROVIDER_MODEL = os.getenv("PROVIDER_MODEL", "gpt-4o-mini")

# Opcional: API key propia para tu endpoint (header: X-Api-Key)
PUBLIC_API_KEY = os.getenv("AI_PUBLIC_API_KEY", "")

# Demo mode (endpoint paralelo sin JWT; requiere header X-Demo-Key)
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
DEMO_API_KEY = os.getenv("DEMO_API_KEY", "evalyze-demo-123")

HTTP_TIMEOUT = 60.0


def _require_config() -> None:
    if not PROVIDER_BASE_URL or not PROVIDER_API_KEY or not PROVIDER_MODEL:
        raise HTTPException(
            status_code=500,
            detail=(
                "AI provider not configured. "
                "Set PROVIDER_BASE_URL, PROVIDER_API_KEY, PROVIDER_MODEL."
            ),
        )


def _check_public_key(x_api_key: str | None) -> None:
    """Valida una API key propia para proteger el endpoint público (opcional)."""
    if not PUBLIC_API_KEY:
        return
    if x_api_key != PUBLIC_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # opcional


class ChatResponse(BaseModel):
    reply: str


@router.get("/health")
def health():
    return {
        "status": "ok",
        "provider_configured": bool(PROVIDER_BASE_URL and PROVIDER_API_KEY),
        "model": PROVIDER_MODEL or None,
        "demo": DEMO_MODE,
    }


def _call_llm(message: str) -> str:
    """
    Llama a un endpoint OpenAI-compatible /v1/chat/completions y retorna el texto.
    Maneja variantes donde content puede ser str o lista de partes.
    """
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
            {"role": "user", "content": (message or "").strip() or "Hola"},
        ],
        "temperature": 0.7,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        content = msg.get("content", "")

        # Algunos proveedores devuelven content como lista de partes
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        text = (content or "(sin respuesta)").strip()
        return text
    except httpx.HTTPStatusError as e:
        # Propaga el status del proveedor para facilitar debug
        raise HTTPException(
            status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Endpoint real (/ai/chat) ===
# Mantén aquí tu futura verificación JWT (cuando migres). Por ahora, valida X-Api-Key si la configuras.
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, x_api_key: str | None = Header(default=None)):
    _check_public_key(x_api_key)
    reply = _call_llm(req.message)
    return {"reply": reply}


# === Endpoint DEMO (/ai/demo-chat) sin JWT; requiere X-Demo-Key ===
@router.post("/demo-chat", response_model=ChatResponse)
def demo_chat(req: ChatRequest, x_demo_key: str | None = Header(default=None)):
    if not DEMO_MODE:
        raise HTTPException(status_code=404, detail="Not found")
    if not (DEMO_API_KEY and x_demo_key == DEMO_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid demo key")

    reply = _call_llm(req.message)
    return {"reply": reply}
