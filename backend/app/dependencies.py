"""
AidFlow AI - Shared Dependencies (Dependency Injection)
Provides: database sessions, authenticated user extraction, admin guards.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.supabase_client import get_supabase_anon_client, get_supabase_client

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Verify the JWT token via Supabase Auth and return the user object.
    Raises 401 if token is invalid or expired.
    """
    supabase = get_supabase_anon_client()

    try:
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        return user_response.user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


async def require_admin(user=Depends(get_current_user)):
    """
    Ensure the current user has admin role.
    Raises 403 if not admin.
    """
    profile = get_supabase_client().table("user_profiles").select("role").eq(
        "user_id", user.id
    ).maybe_single().execute()
    if not profile.data or profile.data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
