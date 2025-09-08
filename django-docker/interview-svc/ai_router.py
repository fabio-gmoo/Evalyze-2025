# ai_cloud_router.py
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
import os, httpx

router = APIRouter(prefix="/ai", tags=["ai"])

# === Config por variables de entorno ===
# Proveedor OpenAI-compatible (p. ej., OpenRouter, Together, Groq, etc.)
# Ejemplos:
#   PROVIDER_BASE_URL=https://api.openai.com       (si usas OpenAI)
#   PROVIDER_BASE_URL=https://openrouter.ai/api
#   PROVIDER_BASE_URL=https://api.together.xyz
#   PROVIDER_BASE_URL=https://api.groq.com/openai
PROVIDER_BASE_URL = os.getenv("PROVIDER_BASE_URL", "").rstrip("/")
PROVIDER_API_KEY  = os.getenv("PROVIDER_API_KEY", "")
PROVIDER_MODEL    = os.getenv("PROVIDER_MODEL", "meta-llama/Llama-3-8b-Instruct")  # cambia según proveedor
# API key propia (opcional) para proteger tu endpoint público
PUBLIC_API_KEY    = os.getenv("AI_PUBLIC_API_KEY", "")  # si vacío, no valida

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
    return {
        "status": "ok",
        "provider": bool(PROVIDER_BASE_URL),
        "model": PROVIDER_MODEL
    }

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, x_api_key: str | None = Header(default=None)):
    _check_public_key(x_api_key)

    if not (PROVIDER_BASE_URL and PROVIDER_API_KEY and PROVIDER_MODEL):
        # modo fallback útil en dev
        return {"reply": f"(Simulado) Recibí: «{req.message}». Configura PROVIDER_*."}

    # La mayoría de proveedores OpenAI-compatibles usan /v1/chat/completions
    url = f"{PROVIDER_BASE_URL}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {PROVIDER_API_KEY}"}
    payload = {
        "model": PROVIDER_MODEL,
        "messages": [
            {"role": "system", "content": "Eres un entrevistador amable y profesional."},
            {"role": "user", "content": req.message.strip() or "Hola"}
        ],
        "temperature": 0.7,
        "stream": False
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            # OpenAI-compatible → respuesta en choices[0].message.content
            text = (data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")) or "(sin respuesta)"
            return {"reply": text.strip()}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
