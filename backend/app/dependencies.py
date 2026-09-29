"""
AidFlow AI - Shared Dependencies (Dependency Injection)
Provides: database sessions, authenticated user extraction, admin guards.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import get_settings
from app.utils.supabase_client import get_supabase_client

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Verify the JWT token via Supabase Auth and return the user object.
    Raises 401 if token is invalid or expired.
    """
    settings = get_settings()
    supabase = get_supabase_client()

    try:
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        return user_response.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


async def require_admin(user=Depends(get_current_user)):
    """
    Ensure the current user has admin role.
    Raises 403 if not admin.
    """
    # Check user metadata for role
    role = (user.user_metadata or {}).get("role", "citizen")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
