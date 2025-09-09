from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from app.routers.health import router as health_router  # type: ignore
from app.routers.chat import router as chat_router  # type: ignore
from infrastructure.config.settings import settings  # type: ignore


app = FastAPI(title="Evalyze Interview Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {"service": "Evalyze Interview Service", "docs": "/docs"}
