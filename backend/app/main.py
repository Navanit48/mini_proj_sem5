"""
AidFlow AI - FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import auth, schemes, eligibility, documents, checklist, analytics, notifications, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    settings = get_settings()
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    yield
    # Shutdown
    print(f"👋 {settings.APP_NAME} shutting down...")


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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(","),
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
