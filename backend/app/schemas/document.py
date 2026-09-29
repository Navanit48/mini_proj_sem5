"""AidFlow AI - Document Schemas"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


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


class OCRResultResponse(BaseModel):
    id: str
    document_id: str
    raw_text: str
    extracted_fields: Dict[str, Any]
    confidence_score: float
    processed_at: datetime


class DocumentDetailResponse(BaseModel):
    document: DocumentResponse
    ocr_result: Optional[OCRResultResponse] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
