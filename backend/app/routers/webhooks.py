"""
AidFlow AI - Webhooks Router
Endpoints for n8n to communicate with the backend.
"""

import hmac

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from app.config import get_settings
from app.utils.supabase_client import get_supabase_client, safe_data

router = APIRouter()


def verify_n8n_webhook(x_n8n_secret: str = Header(None)):
    """Verify the webhook secret from n8n."""
    settings = get_settings()
    if (
        not settings.N8N_WEBHOOK_SECRET
        or not x_n8n_secret
        or not hmac.compare_digest(x_n8n_secret, settings.N8N_WEBHOOK_SECRET)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )
    return True


class ReminderWebhookPayload(BaseModel):
    user_id: str
    items_count: int


@router.post("/n8n/reminder-sent")
async def n8n_reminder_sent(
    payload: ReminderWebhookPayload,
    authorized: bool = Depends(verify_n8n_webhook),
):
    """Callback from n8n after a reminder email is sent."""
    supabase = get_supabase_client()

    supabase.table("notifications").insert({
        "user_id": payload.user_id,
        "type": "reminder",
        "title": "Upcoming Deadlines Reminder",
        "message": f"We sent you an email reminder about {payload.items_count} upcoming checklist items.",
        "is_read": False,
    }).execute()

    return {"status": "success"}


class StatusUpdatePayload(BaseModel):
    user_id: str
    scheme_id: str
    new_status: str


@router.post("/n8n/status-update")
async def n8n_status_update(
    payload: StatusUpdatePayload,
    authorized: bool = Depends(verify_n8n_webhook),
):
    """Callback from n8n when an external application status changes."""
    supabase = get_supabase_client()

    # Get scheme name
    scheme_response = supabase.table("schemes").select("name").eq("id", payload.scheme_id).maybe_single().execute()
    scheme_data = safe_data(scheme_response)
    scheme_name = scheme_data["name"] if scheme_data else "a scheme"

    supabase.table("notifications").insert({
        "user_id": payload.user_id,
        "type": "status_update",
        "title": "Application Status Update",
        "message": f"Your application status for {scheme_name} has changed to: {payload.new_status}",
        "metadata": {"scheme_id": payload.scheme_id, "status": payload.new_status},
        "is_read": False,
    }).execute()

    return {"status": "success"}
