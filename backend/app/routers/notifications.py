"""
AidFlow AI - Notifications Router
Handles in-app user notifications.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.schemas.notification import NotificationListResponse
from app.utils.supabase_client import get_supabase_client
from app.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
async def list_notifications(user=Depends(get_current_user)):
    """List all notifications for the user."""
    supabase = get_supabase_client()

    response = supabase.table("notifications").select("*").eq(
        "user_id", user.id
    ).order("sent_at", desc=True).execute()

    unread_count = sum(1 for n in response.data if not n["is_read"])

    return NotificationListResponse(
        notifications=response.data,
        total=len(response.data),
        unread_count=unread_count,
    )


@router.patch("/{notification_id}/read")
async def mark_as_read(notification_id: str, user=Depends(get_current_user)):
    """Mark a single notification as read."""
    supabase = get_supabase_client()

    response = supabase.table("notifications").update({"is_read": True}).eq(
        "id", notification_id
    ).eq("user_id", user.id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Notification marked as read"}


@router.patch("/read-all")
async def mark_all_as_read(user=Depends(get_current_user)):
    """Mark all unread notifications as read."""
    supabase = get_supabase_client()

    supabase.table("notifications").update({"is_read": True}).eq(
        "user_id", user.id
    ).eq("is_read", False).execute()

    return {"message": "All notifications marked as read"}
