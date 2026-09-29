"""
AidFlow AI - Supabase Client
Singleton client for Supabase interactions.
"""

from supabase import create_client, Client
from functools import lru_cache
from app.config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """Create and return a cached Supabase client instance."""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_anon_client() -> Client:
    """Create a Supabase client with anon key (for auth operations)."""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
