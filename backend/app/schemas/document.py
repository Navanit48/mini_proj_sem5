"""AidFlow AI - Document Schemas"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

ALLOWED_DOC_TYPES = (
    "aadhaar",
    "income_certificate",
    "caste_certificate",
    "bank_passbook",
    "photo",
)

DocType = Literal[
    "aadhaar",
    "income_certificate",
    "caste_certificate",
    "bank_passbook",
    "photo",
]

VerificationStatus = Literal[
    "pending",
    "verified",
    "mismatch",
    "needs_review",
    "preliminary_match",
    "unreadable",
]


class OCRResultResponse(BaseModel):
    id: str
    document_id: str
    raw_text: Optional[str] = None
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = 0.0
    processed_at: Optional[datetime] = None
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
    doc_type: Optional[str] = None
    document_category: Optional[str] = None
    storage_path: Optional[str] = None
    status: str  # pending, uploaded, processing, completed, failed
    file_size_bytes: int = 0
    uploaded_at: datetime
    raw_text: Optional[str] = None
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    ocr_confidence: Optional[float] = None
    verification_status: str = "pending"
    mismatch_details: List[Dict[str, Any]] = Field(default_factory=list)
    verified_at: Optional[datetime] = None
    signed_url: Optional[str] = None
    verification: Optional[OCRResultResponse] = None


class DocumentDetailResponse(BaseModel):
    document: DocumentResponse
    verification: Optional[OCRResultResponse] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


class DocumentStatusResponse(BaseModel):
    id: str
    doc_type: Optional[str] = None
    status: str
    verification_status: str = "pending"
    ocr_confidence: Optional[float] = None
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    mismatch_details: List[Dict[str, Any]] = Field(default_factory=list)
    verified_at: Optional[datetime] = None
    signed_url: Optional[str] = None
    verification: Optional[OCRResultResponse] = None
