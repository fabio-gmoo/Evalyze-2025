from fastapi import APIRouter  # type: ignore
from infrastructure.config.settings import settings  # type: ignore

router = APIRouter(prefix="", tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "model": settings.provider_model}
