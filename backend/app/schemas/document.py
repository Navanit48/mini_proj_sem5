"""AidFlow AI - Document Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class OCRResultResponse(BaseModel):
    id: str
    document_id: str
    raw_text: Optional[str] = None
    extracted_fields: Dict[str, Any]
    confidence_score: float
    processed_at: datetime
    detected_document_type: Optional[str] = None
    document_type_confidence: Optional[float] = None
    verification_status: Optional[str] = None
    validation_summary: Optional[str] = None
    mismatches: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    file_name: str
    file_type: str
    document_category: Optional[str] = None
    status: str  # uploaded, processing, completed, failed
    file_size_bytes: int
    uploaded_at: datetime
    signed_url: Optional[str] = None
    verification: Optional[OCRResultResponse] = None


class DocumentDetailResponse(BaseModel):
    document: DocumentResponse
    verification: Optional[OCRResultResponse] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
