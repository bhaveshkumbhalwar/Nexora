from fastapi import APIRouter

from app.core.config import settings
from app.schemas.chat import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        provider=settings.llm_provider,
        model=settings.llm_model,
        configured=settings.is_configured,
    )
