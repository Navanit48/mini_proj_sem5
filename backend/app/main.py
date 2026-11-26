"""
AidFlow AI - FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.services.ocr_service import init_ocr_engine
from app.routers import (
    analytics,
    applications,
    assistant,
    auth,
    checklist,
    documents,
    eligibility,
    notifications,
    schemes,
    webhooks,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    settings = get_settings()
    logger.info("%s v%s starting", settings.APP_NAME, settings.APP_VERSION)
    init_ocr_engine()
    yield
    # Shutdown
    logger.info("%s shutting down", settings.APP_NAME)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered GovTech platform for discovering government welfare schemes",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ─── CORS Middleware ───
    cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Register Routers ───
    api_prefix = "/api/v1"
    app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["Authentication"])
    app.include_router(schemes.router, prefix=f"{api_prefix}/schemes", tags=["Schemes"])
    app.include_router(eligibility.router, prefix=f"{api_prefix}/eligibility", tags=["Eligibility"])
    app.include_router(documents.router, prefix=f"{api_prefix}/documents", tags=["Documents"])
    app.include_router(checklist.router, prefix=f"{api_prefix}/checklists", tags=["Checklists"])
    app.include_router(analytics.router, prefix=f"{api_prefix}/analytics", tags=["Analytics"])
    app.include_router(notifications.router, prefix=f"{api_prefix}/notifications", tags=["Notifications"])
    app.include_router(webhooks.router, prefix=f"{api_prefix}/webhooks", tags=["Webhooks"])
    app.include_router(assistant.router, prefix=f"{api_prefix}/assistant", tags=["Assistant"])
    app.include_router(applications.router, prefix=f"{api_prefix}/applications", tags=["Applications"])

    # ─── Health Check ───
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    return app


app = create_app()
