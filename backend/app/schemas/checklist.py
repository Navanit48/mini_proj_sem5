"""AidFlow AI - Checklist Schemas"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class ChecklistGenerateRequest(BaseModel):
    scheme_id: str


class ChecklistItemResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    is_completed: bool
    due_date: Optional[date] = None
    sort_order: int
    completed_at: Optional[datetime] = None


class ChecklistItemUpdate(BaseModel):
    is_completed: bool


class ChecklistResponse(BaseModel):
    id: str
    user_id: str
    scheme_id: str
    scheme_name: Optional[str] = None
    status: str  # active, completed
    items: List[ChecklistItemResponse]
    created_at: datetime
    updated_at: datetime


class ChecklistListResponse(BaseModel):
    checklists: List[ChecklistResponse]
    total: int
