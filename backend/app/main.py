from fastapi.responses import JSONResponse
import logging
import os
import sys
from contextlib import asynccontextmanager

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.security import SecurityHeadersMiddleware, cors_settings
from app.config import settings
from app.db.session import init_db
from app.services.seed import auto_seed_initial_data, start_background_seed, seed_state
from app.api.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(settings.PROJECT_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} in {settings.ENVIRONMENT} mode...")
    init_db()
    logger.info("Database tables verified / initialized.")
    # Auto-seed sample ledger, prioritized alerts, investigations & evaluations if DB is empty
    if settings.SEED_IN_BACKGROUND:
        start_background_seed()
    else:
        auto_seed_initial_data()
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SentinelGraph — fact-checked AML investigation assistant",
    lifespan=lifespan
)

# Configure CORS


@app.middleware("http")
async def warming_up_guard(request, call_next):
    """While the demo data is still being created, data routes answer 503 + Retry-After.
    The web app treats that as "server waking up" and retries, instead of showing zeros."""
    path = request.url.path
    if (not seed_state["ready"] and path.startswith(settings.API_PREFIX)
            and not path.startswith(f"{settings.API_PREFIX}/health") and request.method != "OPTIONS"):
        return JSONResponse({"detail": "The server is preparing its demo data. Try again in a few seconds."},
                            status_code=503, headers={"Retry-After": "5"})
    return await call_next(request)


# Added last = outermost, so CORS and security headers also apply to the 503 above.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CORSMiddleware, **cors_settings())

# Mount API routers
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
