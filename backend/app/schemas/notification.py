"""AidFlow AI - Notification Schemas"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str  # reminder, status_update, info
    title: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    is_read: bool
    sent_at: datetime


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
