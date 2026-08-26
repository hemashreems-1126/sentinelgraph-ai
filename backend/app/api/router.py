from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.alerts import router as alerts_router
from app.api.investigations import router as investigations_router
from app.api.audit import router as audit_router
from app.api.evaluation import router as evaluation_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(alerts_router)
api_router.include_router(investigations_router)
api_router.include_router(audit_router)
api_router.include_router(evaluation_router)
