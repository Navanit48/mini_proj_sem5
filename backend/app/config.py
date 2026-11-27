"""
AidFlow AI - Configuration
Loads environment variables with pydantic-settings for type-safe config.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # ─── App ───
    APP_NAME: str = "AidFlow AI"
    APP_VERSION: str = "1.0.0"

    # ─── CORS ───
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ─── Supabase ───
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ─── Groq AI ───
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # ─── PaddleOCR ───
    PADDLE_USE_GPU: bool = False
    PADDLE_LANG: str = "en"
    OCR_MIN_CONFIDENCE: float = 0.80

    # ─── n8n ───
    N8N_WEBHOOK_SECRET: str = ""

    # ─── File Upload ───
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_FILE_TYPES: str = "image/jpeg,image/png,application/pdf"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
