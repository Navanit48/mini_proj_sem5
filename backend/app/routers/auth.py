"""
AidFlow AI - Auth Router
Handles registration, login, logout, and token refresh via Supabase Auth.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.user import UserRegister, UserLogin, AuthResponse, UserProfileResponse, UserProfileUpdate
from app.utils.supabase_client import get_supabase_client
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister):
    """Register a new user via Supabase Auth."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {
                    "full_name": data.full_name,
                    "role": "citizen",
                }
            }
        })

        if not response.user:
            raise HTTPException(status_code=400, detail="Registration failed")

        # Create user profile in our database
        supabase.table("user_profiles").insert({
            "user_id": response.user.id,
            "full_name": data.full_name,
        }).execute()

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id,
            email=response.user.email,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(data: UserLogin):
    """Login via Supabase Auth."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password,
        })

        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id,
            email=response.user.email,
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    """Logout and invalidate session."""
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token."""
    try:
        supabase = get_supabase_client()
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
        ).single().execute()

        return {
            "user_id": user.id,
            "email": user.email,
            "role": (user.user_metadata or {}).get("role", "citizen"),
            "profile": profile.data,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
