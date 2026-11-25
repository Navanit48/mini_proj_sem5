"""Background OCR and preliminary document verification processing."""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings
from app.services.document_verification import verify_document
from app.utils.ocr_compat import save_ocr_verification
from app.utils.storage import download_file
from app.utils.supabase_client import get_supabase_client, safe_data

logger = logging.getLogger(__name__)
_ocr_engine = None


def get_ocr_engine():
    """Load PaddleOCR only when a document is actually processed."""
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR

        settings = get_settings()
        _ocr_engine = PaddleOCR(
            use_angle_cls=True,
            lang=settings.PADDLE_LANG,
            use_gpu=settings.PADDLE_USE_GPU,
            show_log=False,
        )
    return _ocr_engine


def _read_ocr_output(result: Any) -> tuple[str, float]:
    lines: list[str] = []
    confidences: list[float] = []
    for page in result or []:
        if not isinstance(page, (list, tuple)):
            continue
        for line in page:
            try:
                text, confidence = line[1][0], float(line[1][1])
            except (IndexError, TypeError, ValueError):
                continue
            if text:
                lines.append(str(text))
                confidences.append(confidence)
    return "\n".join(lines), sum(confidences) / len(confidences) if confidences else 0.0


def _extract_text_from_file(file_bytes: bytes, file_type: str) -> tuple[str, float]:
    """Run local PaddleOCR on an image or PDF (converting PDF pages to images first)."""
    engine = get_ocr_engine()
    temp_paths: list[str] = []
    try:
        if file_type == "application/pdf":
            from pdf2image import convert_from_bytes

            images = convert_from_bytes(file_bytes, dpi=200)
            page_texts: list[str] = []
            page_confidences: list[float] = []
            for image in images:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as page_file:
                    image.save(page_file, format="JPEG")
                    temp_paths.append(page_file.name)
                page_text, page_conf = _read_ocr_output(engine.ocr(temp_paths[-1], cls=True))
                if page_text:
                    page_texts.append(page_text)
                    page_confidences.append(page_conf)
            avg_conf = sum(page_confidences) / len(page_confidences) if page_confidences else 0.0
            return "\n".join(page_texts), avg_conf

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(file_bytes)
            temp_paths.append(temp_file.name)
        return _read_ocr_output(engine.ocr(temp_paths[-1], cls=True))
    finally:
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)


def process_document_ocr(
    document_id: str,
    user_id: str,
    storage_path: str,
    file_type: str,
    declared_type: str = "general",
) -> None:
    """Run local OCR, compare explicit fields with the user's saved profile, and persist a preliminary result."""
    supabase = get_supabase_client()
    try:
        supabase.table("documents").update({"status": "processing"}).eq(
            "id", document_id
        ).eq("user_id", user_id).execute()

        file_bytes = download_file(storage_path)
        ocr_text, ocr_confidence = _extract_text_from_file(file_bytes, file_type)
        profile_response = supabase.table("user_profiles").select(
            "full_name,date_of_birth,gender,state,district,category,annual_income,land_holding_acres"
        ).eq("user_id", user_id).maybe_single().execute()
        profile = safe_data(profile_response) or {}
        verification = verify_document(ocr_text, declared_type, profile, ocr_confidence)

        save_ocr_verification(
            supabase,
            document_id,
            user_id,
            "completed",
            {
                # Raw OCR can contain identity and financial data. Persist only the fields needed for review.
                "raw_text": None,
                "extracted_fields": verification["extracted_fields"],
                "confidence_score": verification["confidence_score"],
                "detected_document_type": verification["detected_document_type"],
                "document_type_confidence": verification["document_type_confidence"],
                "verification_status": verification["verification_status"],
                "validation_summary": verification["validation_summary"],
                "mismatches": verification["mismatches"],
                "warnings": verification["warnings"],
                "processed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    except Exception:
        logger.exception("Preliminary document verification failed for document %s", document_id)
        try:
            save_ocr_verification(
                supabase,
                document_id,
                user_id,
                "failed",
                {
                    "raw_text": None,
                    "extracted_fields": {},
                    "confidence_score": 0,
                    "detected_document_type": declared_type,
                    "document_type_confidence": 0,
                    "verification_status": "unreadable",
                    "validation_summary": "Preliminary verification could not be completed. Review the file or upload a clearer scan.",
                    "mismatches": [],
                    "warnings": ["OCR processing failed; no document details were confirmed."],
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception:
            logger.exception("Could not save failure state for document %s", document_id)

    try:
        from app.services.application_service import refresh_applications_for_document

        refresh_applications_for_document(supabase, user_id, document_id)
    except Exception:
        logger.exception("Could not refresh application status after document processing")
