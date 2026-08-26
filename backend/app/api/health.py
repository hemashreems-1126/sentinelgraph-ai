import datetime
from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "llm_mode": "mock_offline" if settings.is_mock_llm else "live_groq",
        "groq_model": settings.GROQ_MODEL,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
