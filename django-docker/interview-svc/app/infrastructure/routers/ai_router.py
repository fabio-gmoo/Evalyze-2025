# //interview-svc/app/infrastructure/routers/ai_router.py
import httpx  # type: ignore
import json
import os
from fastapi import APIRouter, Header, HTTPException  # type: ignore
from app.domain.models import (
    ChatRequest,
    ChatResponse,
    VacancyDraftIn,
    VacancyDraftOut,
    StartConversationReq,
    StartConversationRes,
)  # type: ignore
from app.domain.services import ChatService  # type: ignore
from app.infrastructure.ai_provider import HttpLLMAdapter  # type: ignore
from app.infrastructure.content_moderator import get_content_moderator  # type: ignore
from dotenv import load_dotenv  # type: ignore
import logging

load_dotenv()  # Cargar variables de entorno desde el archivo .env
logger = logging.getLogger(__name__)

# --- Configuración de seguridad ---
PUBLIC_API_KEY = os.getenv("AI_PUBLIC_API_KEY", "")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
DEMO_API_KEY = os.getenv("DEMO_API_KEY", "evalyze-demo-123")

CONTENT_MODERATION_ENABLED = (
    os.getenv("CONTENT_MODERATION_ENABLED", "true").lower() == "true"
)
CONTENT_MODERATION_REQUIRE_CONSENSUS = (
    os.getenv("CONTENT_MODERATION_REQUIRE_CONSENSUS",
              "false").lower() == "true"
)
PERSPECTIVE_THRESHOLD = float(os.getenv("PERSPECTIVE_THRESHOLD", "0.7"))


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
            "moderation": CONTENT_MODERATION_ENABLED,
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
        """Genera un borrador con IA"""
        _check_public_key(x_api_key)

        # ========== MODERACIÓN DE CONTENIDO ==========
        moderator = get_content_moderator()

        # Moderar SOLO el puesto (lo más importante)
        moderation = moderator.moderate(
            text=req.puesto,
            require_consensus=False,
            perspective_threshold=0.7,
        )

        # Si está flagged, RECHAZAR INMEDIATAMENTE
        if moderation.flagged or not moderation.allowed:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "El contenido de la vacante no es apropiado",
                    "detail": moderation.detail,
                    "categories": moderation.categories,
                    "confidence": moderation.confidence,
                },
            )

        # Prompt al LLM (tu código original)
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

        # Conexión con el LLM (tu código original)
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

            # Parseo JSON (tu código original)
            try:
                raw = json.loads(content)
            except Exception:
                start = content.find("{")
                end = content.rfind("}")
                if start >= 0 and end > start:
                    raw = json.loads(content[start: end + 1])
                else:
                    raise HTTPException(
                        status_code=502, detail="El modelo no devolvió JSON válido."
                    )

            # Normalizar respuesta (tu código original)
            out = VacancyDraftOut(
                puesto=raw.get("puesto", req.puesto),
                descripcion_sugerida=raw.get(
                    "descripcion_sugerida", req.descripcion),
                requisitos_sugeridos=raw.get("requisitos_sugeridos", []),
            )

            logger.info(f"✅ Draft generado exitosamente para: {req.puesto}")
            return out

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Error HTTP en generación: {
                         e.response.status_code}")
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.text
            )
        except Exception as e:
            logger.error(f"❌ Error generando draft: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/vacants/save", response_model=VacancyDraftOut)
    async def save_vacant(
        req: VacancyDraftIn, x_api_key: str | None = Header(default=None)
    ):
        """
        Guarda una vacante editada y aprobada por el usuario en Django.
        """
        _check_public_key(x_api_key)

        # Realizamos la llamada a Django para guardar los datos
        django_url = "http://localhost:8000/vacantes/guardar/"
        headers = {"Content-Type": "application/json"}

        # Datos para guardar
        data = {
            "id": req.id,  # Asegúrate de pasar el ID de la vacante a guardar
            "puesto": req.puesto,
            "descripcion": req.descripcion_sugerida,
            "requisitos": req.requisitos_sugeridos,
            "ubicacion": req.ubicacion,
            "salario": req.salario,
            "tipo_contrato": req.tipo_contrato,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(django_url, json=data, headers=headers)

        if response.status_code == 201:
            return {
                "status": "Vacante guardada con éxito",
                "id": response.json().get("id"),
            }
        else:
            raise HTTPException(
                status_code=400, detail="Error al guardar la vacante en Django"
            )

    @router.post("/candidate-conversations/start", response_model=StartConversationRes)
    async def start_candidate_conversations(
        req: StartConversationReq, x_api_key: str | None = Header(default=None)
    ):
        """
        Initiates a conversation for all applied candidates based on the generated interview questions.
        """
        _check_public_key(x_api_key)

        logger.info(
            f"🚀 Starting conversations for {len(req.candidates)} candidates "
            f"for vacancy ID {req.vacancy_id}: {req.vacancy_title}"
        )

        # --- LOGIC TO START CONVERSATION ---

        # 1. In a real system, you would iterate over req.candidates.
        # 2. For each candidate, you'd save the interview_questions to your DB.
        # 3. You would then use the chat_service (or a new dedicated service)
        #    to generate the FIRST message using the interview_questions as a system prompt.
        #    The system prompt would instruct the LLM (via HttpLLMAdapter.chat) to
        #    start the conversation with the first question.

        started_ids = []
        for candidate in req.candidates:
            # Example: Imagine this line initiates a job or saves the chat history start
            # For demonstration, we just log and collect the ID
            logger.info(
                f"   -> Initiating chat for candidate {
                    candidate.id}: {candidate.name}"
            )
            started_ids.append(candidate.id)

        # You would typically call chat_service.handle_chat or a new service here
        # to generate the initial greeting/first question.

        return StartConversationRes(
            status="Initiation complete",
            total_candidates=len(req.candidates),
            started_chats=started_ids,
        )

    return router
