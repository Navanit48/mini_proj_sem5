"""
AidFlow AI - Auth Router
Handles registration, login, logout, and token refresh via Supabase Auth.
"""

import logging

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.user import UserRegister, UserLogin, AuthResponse
from app.utils.supabase_client import get_supabase_client, get_supabase_anon_client
from app.dependencies import get_current_user, security

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister):
    """Register a new user via Supabase Auth."""
    stage = "Supabase client initialization"
    try:
        auth_client = get_supabase_anon_client()
        supabase = get_supabase_client()
        stage = "Supabase Auth sign_up"
        response = auth_client.auth.sign_up({
            "email": data.email,
            "password": data.password,
        })

        if not response.user:
            logger.error("Registration returned no Supabase Auth user")
            raise HTTPException(status_code=400, detail="Registration failed")

        # Create user profile in our database
        stage = "user_profiles upsert"
        supabase.table("user_profiles").upsert({
            "user_id": response.user.id,
            "full_name": data.full_name,
        }, on_conflict="user_id").execute()

        return AuthResponse(
            access_token=response.session.access_token if response.session else None,
            refresh_token=response.session.refresh_token if response.session else None,
            user_id=response.user.id,
            email=response.user.email,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Registration failed during %s", stage)
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/login", response_model=AuthResponse)
async def login(data: UserLogin):
    """Login via Supabase Auth."""
    try:
        auth_client = get_supabase_anon_client()
        response = auth_client.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password,
        })

        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not response.session:
            raise HTTPException(status_code=401, detail="Login did not create a session")

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id,
            email=response.user.email,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials") from e


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user=Depends(get_current_user),
):
    """Logout and invalidate session."""
    try:
        get_supabase_client().auth.admin.sign_out(credentials.credentials, "global")
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Logout failed") from e


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token."""
    try:
        supabase = get_supabase_anon_client()
        response = supabase.auth.refresh_session(refresh_token)

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id,
            email=response.user.email,
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    """Get current authenticated user's profile."""
    try:
        supabase = get_supabase_client()
        profile = supabase.table("user_profiles").select("*").eq(
            "user_id", user.id
        ).maybe_single().execute()

        if not profile.data:
            raise HTTPException(status_code=404, detail="User profile not found")

        return {
            "user_id": user.id,
            "email": user.email,
            "role": profile.data["role"],
            "profile": profile.data,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not load user profile") from e
