from fastapi import APIRouter, Depends, Header  # type: ignore
from application.dto import ChatIn
from application.use_cases.chat_with_ai import ChatWithAi
from infrastructure.auth.jwt_verifier import JwtVerifier
from infrastructure.llm.openai_client import OpenAiCompatClient
from infrastructure.persistence.supabase_repo import SupabaseMessageRepo

router = APIRouter(prefix="/ai", tags=["ai"])

# Factories simples (podrías usar un contenedor DI si quieres)


def get_use_case() -> ChatWithAi:
    llm = OpenAiCompatClient()
    repo = SupabaseMessageRepo()
    return ChatWithAi(llm, repo)


def get_auth():
    return JwtVerifier()


@router.post("/chat")
def chat(
    input: ChatIn,
    authorization: str | None = Header(default=None),
    auth: JwtVerifier = Depends(get_auth),
    uc: ChatWithAi = Depends(get_use_case),
):
    claims = auth.verify(authorization)  # levanta 401 si no válido
    user_sub = claims.get("sub") or claims.get("user_id")
    return uc.execute(input, user_sub)
