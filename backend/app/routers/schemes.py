"""
AidFlow AI - Schemes Router
CRUD operations for government welfare schemes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.schemas.scheme import SchemeCreate, SchemeUpdate, SchemeResponse, SchemeListResponse
from app.utils.supabase_client import get_supabase_client
from app.dependencies import get_current_user, require_admin
import re

router = APIRouter()


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text


@router.get("", response_model=SchemeListResponse)
async def list_schemes(
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=50),
    category: Optional[str] = None,
    state: Optional[str] = None,
    ministry: Optional[str] = None,
    user=Depends(get_current_user),
):
    """List all active schemes with pagination and filters."""
    supabase = get_supabase_client()

    query = supabase.table("schemes").select("*", count="exact").eq("is_active", True)

    if category:
        query = query.eq("category", category)
    if ministry:
        query = query.eq("ministry", ministry)
    if state:
        query = query.contains("target_states", [state])

    # Pagination
    start = (page - 1) * per_page
    end = start + per_page - 1
    query = query.range(start, end).order("created_at", desc=True)

    response = query.execute()

    return SchemeListResponse(
        schemes=response.data,
        total=response.count or 0,
        page=page,
        per_page=per_page,
    )


@router.get("/search")
async def search_schemes(
    q: str = Query(..., min_length=2),
    user=Depends(get_current_user),
):
    """Full-text search across schemes."""
    supabase = get_supabase_client()
    response = supabase.table("schemes").select("*").or_(
        f"name.ilike.%{q}%,description.ilike.%{q}%,ministry.ilike.%{q}%"
    ).eq("is_active", True).limit(20).execute()

    return {"results": response.data, "count": len(response.data)}


@router.get("/{scheme_id}", response_model=SchemeResponse)
async def get_scheme(scheme_id: str, user=Depends(get_current_user)):
    """Get single scheme by ID."""
    supabase = get_supabase_client()
    response = supabase.table("schemes").select("*").eq("id", scheme_id).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Scheme not found")

    return response.data


@router.post("", response_model=SchemeResponse, status_code=201)
async def create_scheme(data: SchemeCreate, admin=Depends(require_admin)):
    """Create a new scheme (Admin only)."""
    supabase = get_supabase_client()

    scheme_data = data.model_dump()
    scheme_data["slug"] = slugify(data.name)
    scheme_data["is_active"] = True

    response = supabase.table("schemes").insert(scheme_data).execute()
    return response.data[0]


@router.put("/{scheme_id}", response_model=SchemeResponse)
async def update_scheme(scheme_id: str, data: SchemeUpdate, admin=Depends(require_admin)):
    """Update a scheme (Admin only)."""
    supabase = get_supabase_client()

    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data:
        update_data["slug"] = slugify(update_data["name"])

    response = supabase.table("schemes").update(update_data).eq("id", scheme_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Scheme not found")

    return response.data[0]


@router.delete("/{scheme_id}")
async def delete_scheme(scheme_id: str, admin=Depends(require_admin)):
    """Soft-delete a scheme (Admin only)."""
    supabase = get_supabase_client()
    supabase.table("schemes").update({"is_active": False}).eq("id", scheme_id).execute()
    return {"message": "Scheme deactivated"}
