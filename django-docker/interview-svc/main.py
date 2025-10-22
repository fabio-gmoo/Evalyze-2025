# interview-svc/main.py
from fastapi import FastAPI  # type: ignore
from app.domain.services import ChatService  # type: ignore
from app.infrastructure.ai_provider import HttpLLMAdapter  # type: ignore
from app.infrastructure.routers.ai_router import get_ai_router  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore


def create_app() -> FastAPI:
    app = FastAPI(title="AI API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:4200",
            "http://127.0.0.1:4200",
            "https://evalyze-production.up.railway.app/",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    llm_adapter = HttpLLMAdapter()
    chat_service = ChatService(llm=llm_adapter)
    app.include_router(get_ai_router(chat_service))
    return app


app = create_app()
