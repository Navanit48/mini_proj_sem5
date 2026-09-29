"""AidFlow AI - Eligibility Schemas"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class EligibilityCheckRequest(BaseModel):
    """User profile data submitted for eligibility checking."""
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    occupation: Optional[str] = None
    category: Optional[str] = None
    annual_income: Optional[float] = None
    land_holding_acres: Optional[float] = None
    is_bpl: Optional[bool] = None
    is_disabled: Optional[bool] = None
    additional_data: Optional[Dict[str, Any]] = None


class EligibilityResultItem(BaseModel):
    scheme_id: str
    scheme_name: str
    match_percentage: float
    matched_rules: List[str]
    failed_rules: List[str]


class EligibilityCheckResponse(BaseModel):
    check_id: str
    matched_count: int
    results: List[EligibilityResultItem]
    checked_at: datetime


class EligibilityHistoryResponse(BaseModel):
    checks: List[EligibilityCheckResponse]
    total: int
