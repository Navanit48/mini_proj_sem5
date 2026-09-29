"""
AidFlow AI - Configuration
Loads environment variables with pydantic-settings for type-safe config.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ─── App ───
    APP_NAME: str = "AidFlow AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    BACKEND_PORT: int = 8000
    SECRET_KEY: str = "change-me-in-production"

    # ─── CORS ───
    CORS_ORIGINS: str = "http://localhost:5173"

    # ─── Supabase ───
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ─── Database ───
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aidflow"

    # ─── Groq AI ───
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ─── PaddleOCR ───
    PADDLE_USE_GPU: bool = False
    PADDLE_LANG: str = "en"

    # ─── n8n ───
    N8N_BASE_URL: str = "http://n8n:5678"
    N8N_API_KEY: str = ""
    N8N_WEBHOOK_SECRET: str = ""

    # ─── File Upload ───
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = "image/jpeg,image/png,application/pdf"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
