from fastapi import APIRouter, Header, HTTPException  # type: ignore
from app.domain.models import ChatRequest, ChatResponse, VacancyDraftIn, VacancyDraftOut  # type: ignore
from app.domain.services import ChatService  # type: ignore
from app.infrastructure.ai_provider import HttpLLMAdapter  # type: ignore
import os
import json
import httpx  # type: ignore

# --- Configuración de seguridad ---
PUBLIC_API_KEY = os.getenv("AI_PUBLIC_API_KEY", "")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
DEMO_API_KEY = os.getenv("DEMO_API_KEY", "evalyze-demo-123")


def _check_public_key(x_api_key: str | None) -> None:
    """Valida una API key propia para proteger el endpoint público (opcional)."""
    if not PUBLIC_API_KEY:  # si no está configurada → endpoint libre
        return
    if x_api_key != PUBLIC_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def get_ai_router(chat_service: ChatService) -> APIRouter:
    router = APIRouter(prefix="/ai", tags=["ai"])

    @router.get("/health")
    def health():
        return {
            "status": "ok",
            "model": "configured",
            "demo": DEMO_MODE,
            "public_protected": bool(PUBLIC_API_KEY),
        }

    @router.post("/chat", response_model=ChatResponse)
    def chat(req: ChatRequest, x_api_key: str | None = Header(default=None)):
        _check_public_key(x_api_key)
        return chat_service.handle_chat(req)

    @router.post("/demo-chat", response_model=ChatResponse)
    def demo_chat(req: ChatRequest, x_demo_key: str | None = Header(default=None)):
        if not DEMO_MODE:
            raise HTTPException(status_code=404, detail="Not found")
        if not (DEMO_API_KEY and x_demo_key == DEMO_API_KEY):
            raise HTTPException(status_code=401, detail="Invalid demo key")

        return chat_service.handle_chat(req)

    @router.post("/vacants/draft", response_model=VacancyDraftOut)
    def draft_vacant(req: VacancyDraftIn, x_api_key: str | None = Header(default=None)):
        """
        Genera un borrador con IA (descripcion_sugerida + requisitos_sugeridos).
        NO persiste. El front puede editar y luego guardar en Django.
        """
        _check_public_key(x_api_key)

        # Prompt al LLM
        system_msg = (
            "Eres un reclutador técnico. Devuelve SOLO JSON con campos: "
            "{'puesto','descripcion_sugerida','requisitos_sugeridos','notas'}."
            "Requisitos deben ser concretos, accionables y medibles."
        )

        user_msg = f"""
        Puesto: {req.puesto}
        Descripción (base): {req.descripcion}
        Ubicación: {req.ubicacion}
        Salario (opcional): {req.salario or "-"}
        Tipo de contrato (opcional): {req.tipo_contrato or "-"}
        """

        # Conexión con el LLM
        llm = HttpLLMAdapter()

        payload = {
            "model": llm.model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            "temperature": 0.5,
            "stream": False,
        }

        try:
            headers = {
                "Authorization": f"Bearer {llm.api_key}",
                "Content-Type": "application/json",
            }
            with httpx.Client(timeout=60.0) as client:
                r = client.post(
                    f"{llm.base_url}/v1/chat/completions", headers=headers, json=payload
                )
                r.raise_for_status()
                data = r.json()

                content = (
                    (data.get("choices") or [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )

            # Parseo robusto del JSON devuelto
            try:
                raw = json.loads(content)
            except Exception:
                # Fallback: intentar extraer el JSON entre llaves
                start = content.find("{")
                end = content.rfind("}")
                if start >= 0 and end > start:
                    raw = json.loads(content[start: end + 1])
                else:
                    raise HTTPException(
                        status_code=502, detail="El modelo no devolvió JSON válido."
                    )

            # Normalizar claves con defaults
            out = VacancyDraftOut(
                puesto=raw.get("puesto", req.puesto),
                descripcion_sugerida=raw.get(
                    "descripcion_sugerida", req.descripcion),
                requisitos_sugeridos=raw.get("requisitos_sugeridos", []),
            )
            return out

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.text
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
