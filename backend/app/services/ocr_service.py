"""
AidFlow AI - OCR Service
Wraps PaddleOCR for text extraction and integrates with AI Service for structuring.
"""

from app.utils.supabase_client import get_supabase_client
from app.utils.storage import download_file
from app.services.ai_service import extract_fields_from_ocr
from app.config import get_settings
import tempfile
import os
import uuid

# Lazy load PaddleOCR to avoid massive memory usage on startup
_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR
        settings = get_settings()
        _ocr_engine = PaddleOCR(
            use_angle_cls=True, 
            lang=settings.PADDLE_LANG, 
            use_gpu=settings.PADDLE_USE_GPU,
            show_log=False
        )
    return _ocr_engine


async def process_document_ocr(document_id: str, storage_path: str, file_type: str):
    """
    Background task: Download file, run OCR, extract fields via AI, save results.
    """
    supabase = get_supabase_client()
    
    try:
        # Update status
        supabase.table("documents").update({"status": "processing"}).eq("id", document_id).execute()
        
        # Download file bytes
        file_bytes = download_file(storage_path)
        
        # PaddleOCR requires a file path on disk, not bytes directly for some formats
        # We'll use a temporary file
        ext = ".pdf" if "pdf" in file_type else ".jpg"
        temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}{ext}")
        
        with open(temp_path, "wb") as f:
            f.write(file_bytes)
            
        # Get engine and run OCR
        ocr = get_ocr_engine()
        result = ocr.ocr(temp_path, cls=True)
        
        # Parse PaddleOCR output
        raw_text_parts = []
        confidence_sum = 0
        word_count = 0
        
        # result is a list of lists (pages -> lines)
        if result and result[0]:
            for line in result[0]:
                if len(line) >= 2 and len(line[1]) >= 2:
                    text = line[1][0]
                    confidence = line[1][1]
                    raw_text_parts.append(text)
                    confidence_sum += confidence
                    word_count += 1
                    
        raw_text = "\n".join(raw_text_parts)
        avg_confidence = (confidence_sum / word_count) if word_count > 0 else 0
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        # Get document category for AI hint
        doc = supabase.table("documents").select("document_category").eq("id", document_id).single().execute()
        category = doc.data.get("document_category", "unknown") if doc.data else "unknown"
        
        # Use AI to extract structured fields
        extracted_fields = extract_fields_from_ocr(raw_text, category)
        
        # Save results
        supabase.table("ocr_results").insert({
            "document_id": document_id,
            "raw_text": raw_text,
            "extracted_fields": extracted_fields,
            "confidence_score": float(avg_confidence)
        }).execute()
        
        # Update document status
        supabase.table("documents").update({"status": "completed"}).eq("id", document_id).execute()
        
    except Exception as e:
        print(f"OCR Error for document {document_id}: {str(e)}")
        # Update document status to failed
        supabase.table("documents").update({"status": "failed"}).eq("id", document_id).execute()
