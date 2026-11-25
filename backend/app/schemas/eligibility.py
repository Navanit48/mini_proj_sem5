"""AidFlow AI - Eligibility Schemas"""
from pydantic import BaseModel, Field
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
    ai_recommendation: Optional["AIRecommendation"] = None


class RecommendedDocument(BaseModel):
    name: str
    category: str
    uploaded: bool
    generic: bool = False


class RecommendationAction(BaseModel):
    label: str
    kind: str
    href: str
    external: bool = False


class ChecklistProgress(BaseModel):
    total: int
    completed: int


class PriorityBadge(BaseModel):
    stars: int
    label: str
    class_: str = Field(alias="class")


class AIRecommendation(BaseModel):
    status: str
    reasons: List[str]
    recommendation: str
    improve_eligibility: List[str]
    confidence_score: float
    priority_score: Optional[float] = None
    priority: Optional[PriorityBadge] = None
    recommended_documents: List[RecommendedDocument] = Field(default_factory=list)
    next_action: Optional[RecommendationAction] = None
    checklist_progress: Optional[ChecklistProgress] = None


class AISummary(BaseModel):
    profile_strength: int
    eligible_schemes: List[str]
    near_misses: List[str]
    evaluated_count: int


class EligibilityCheckResponse(BaseModel):
    check_id: str
    matched_count: int
    results: List[EligibilityResultItem]
    checked_at: datetime
    ai_summary: Optional[AISummary] = None


class EligibilityHistoryResponse(BaseModel):
    checks: List[EligibilityCheckResponse]
    total: int


EligibilityResultItem.model_rebuild()
