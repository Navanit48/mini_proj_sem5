"""AidFlow AI - Scheme Schemas"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class SchemeCreate(BaseModel):
    name: str
    description: str
    ministry: str
    category: str
    target_states: List[str] = []
    benefits_summary: str
    eligibility_summary: str
    application_url: Optional[str] = None
    deadline: Optional[date] = None


class SchemeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ministry: Optional[str] = None
    category: Optional[str] = None
    target_states: Optional[List[str]] = None
    benefits_summary: Optional[str] = None
    eligibility_summary: Optional[str] = None
    application_url: Optional[str] = None
    deadline: Optional[date] = None
    is_active: Optional[bool] = None


class SchemeResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    ministry: str
    category: str
    target_states: List[str]
    benefits_summary: str
    eligibility_summary: str
    application_url: Optional[str] = None
    deadline: Optional[date] = None
    is_active: bool
    created_at: datetime


class SchemeListResponse(BaseModel):
    schemes: List[SchemeResponse]
    total: int
    page: int
    per_page: int
