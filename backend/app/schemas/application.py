"""API schemas for AidFlow application packages and tracking."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ApplicationStatus = Literal[
    "submitted",
    "under_review",
    "ai_document_verification",
    "ready_for_government_submission",
]


class ApplicationPreviewRequest(BaseModel):
    scheme_id: str
    eligibility_check_id: str | None = None


class ApplicationSubmitRequest(BaseModel):
    scheme_id: str
    profile_overrides: dict[str, Any] = Field(default_factory=dict)
    document_ids: list[str] = Field(default_factory=list, max_length=20)
    eligibility_check_id: str | None = None


class ApplicationDocument(BaseModel):
    id: str
    document_id: str | None = None
    file_name: str
    document_category: str | None = None
    status: str
    verification_status: str | None = None
    confidence_score: float | None = None
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    uploaded_at: datetime | str | None = None


class ApplicationEvent(BaseModel):
    status: str
    description: str
    progress: int
    occurred_at: datetime | str


class ExternalApplicationStage(BaseModel):
    status: Literal["not_started"] = "not_started"
    title: str
    description: str
    occurred_at: None = None
    progress: int = 0


class ApplicationResponse(BaseModel):
    id: str
    application_code: str
    user_id: str
    scheme_id: str
    scheme_name: str
    status: ApplicationStatus
    submitted_at: datetime | str
    updated_at: datetime | str
    progress: int
    profile_snapshot: dict[str, Any]
    eligibility_snapshot: dict[str, Any] = Field(default_factory=dict)
    documents: list[ApplicationDocument] = Field(default_factory=list)
    timeline: list[ApplicationEvent] = Field(default_factory=list)
    external_stages: list[ExternalApplicationStage] = Field(default_factory=list)


class ApplicationListResponse(BaseModel):
    applications: list[ApplicationResponse]
    total: int


class ApplicationPreviewResponse(BaseModel):
    scheme: dict[str, Any]
    profile: dict[str, Any]
    eligibility: dict[str, Any] = Field(default_factory=dict)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    missing_profile_fields: list[str] = Field(default_factory=list)
    notice: str
