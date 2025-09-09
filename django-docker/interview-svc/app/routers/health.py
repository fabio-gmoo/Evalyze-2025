from fastapi import APIRouter  # type: ignore
from infrastructure.config.settings import settings

router = APIRouter(prefix="", tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "model": settings.provider_model}
