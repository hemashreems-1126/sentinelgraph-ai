import datetime
from fastapi import APIRouter
from app.config import settings
from app.services.seed import seed_state

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
        "data_ready": seed_state["ready"],
        "data_stage": seed_state["stage"],
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
