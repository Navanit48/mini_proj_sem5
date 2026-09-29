"""
AidFlow AI - Checklist Router
AI-generated application checklists per scheme.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.schemas.checklist import (
    ChecklistGenerateRequest, ChecklistResponse,
    ChecklistListResponse, ChecklistItemUpdate,
)
from app.utils.supabase_client import get_supabase_client
from app.dependencies import get_current_user
from app.services.checklist_service import generate_checklist_items
from datetime import datetime

router = APIRouter()


@router.post("/generate", response_model=ChecklistResponse, status_code=201)
async def generate_checklist(data: ChecklistGenerateRequest, user=Depends(get_current_user)):
    """Generate an AI-powered checklist for a scheme application."""
    supabase = get_supabase_client()

    # Get scheme details
    scheme = supabase.table("schemes").select("*").eq("id", data.scheme_id).single().execute()
    if not scheme.data:
        raise HTTPException(status_code=404, detail="Scheme not found")

    # Check if checklist already exists
    existing = supabase.table("checklists").select("*").eq(
        "user_id", user.id
    ).eq("scheme_id", data.scheme_id).execute()

    if existing.data:
        raise HTTPException(status_code=409, detail="Checklist already exists for this scheme")

    # Generate checklist items using AI
    items = await generate_checklist_items(scheme.data)

    # Create checklist
    checklist = supabase.table("checklists").insert({
        "user_id": user.id,
        "scheme_id": data.scheme_id,
        "status": "active",
    }).execute()

    checklist_id = checklist.data[0]["id"]

    # Insert items
    for idx, item in enumerate(items):
        supabase.table("checklist_items").insert({
            "checklist_id": checklist_id,
            "title": item["title"],
            "description": item.get("description", ""),
            "is_completed": False,
            "due_date": item.get("due_date"),
            "sort_order": idx,
        }).execute()

    # Fetch full checklist with items
    return await _get_checklist(checklist_id, user.id)


@router.get("", response_model=ChecklistListResponse)
async def list_checklists(user=Depends(get_current_user)):
    """List all checklists for the current user."""
    supabase = get_supabase_client()

    checklists = supabase.table("checklists").select(
        "*, checklist_items(*), schemes(name)"
    ).eq("user_id", user.id).order("created_at", desc=True).execute()

    formatted = []
    for cl in checklists.data:
        cl["scheme_name"] = cl.get("schemes", {}).get("name")
        cl["items"] = cl.pop("checklist_items", [])
        formatted.append(cl)

    return ChecklistListResponse(checklists=formatted, total=len(formatted))


@router.get("/{checklist_id}", response_model=ChecklistResponse)
async def get_checklist(checklist_id: str, user=Depends(get_current_user)):
    """Get a single checklist with items."""
    return await _get_checklist(checklist_id, user.id)


@router.patch("/{checklist_id}/items/{item_id}")
async def update_checklist_item(
    checklist_id: str,
    item_id: str,
    data: ChecklistItemUpdate,
    user=Depends(get_current_user),
):
    """Mark a checklist item as complete or incomplete."""
    supabase = get_supabase_client()

    # Verify checklist ownership
    checklist = supabase.table("checklists").select("*").eq(
        "id", checklist_id
    ).eq("user_id", user.id).single().execute()

    if not checklist.data:
        raise HTTPException(status_code=404, detail="Checklist not found")

    update_data = {"is_completed": data.is_completed}
    if data.is_completed:
        update_data["completed_at"] = datetime.utcnow().isoformat()
    else:
        update_data["completed_at"] = None

    supabase.table("checklist_items").update(update_data).eq("id", item_id).execute()

    # Check if all items complete → update checklist status
    items = supabase.table("checklist_items").select("is_completed").eq(
        "checklist_id", checklist_id
    ).execute()

    all_complete = all(item["is_completed"] for item in items.data)
    if all_complete:
        supabase.table("checklists").update({"status": "completed"}).eq("id", checklist_id).execute()

    return {"message": "Item updated", "is_completed": data.is_completed}


async def _get_checklist(checklist_id: str, user_id: str) -> dict:
    """Internal helper to fetch a full checklist."""
    supabase = get_supabase_client()

    cl = supabase.table("checklists").select(
        "*, checklist_items(*), schemes(name)"
    ).eq("id", checklist_id).eq("user_id", user_id).single().execute()

    if not cl.data:
        raise HTTPException(status_code=404, detail="Checklist not found")

    cl.data["scheme_name"] = cl.data.get("schemes", {}).get("name")
    cl.data["items"] = cl.data.pop("checklist_items", [])
    return cl.data
