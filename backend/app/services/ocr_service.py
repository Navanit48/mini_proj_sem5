"""Image preprocessing and PaddleOCR text extraction service."""

from __future__ import annotations

import io
import logging
import os
import re
import tempfile
from datetime import datetime, timezone
from typing import Any

import cv2
import numpy as np

from app.config import get_settings
from app.services.checklist_service import mark_matching_checklist_tasks_complete
from app.services.document_verifier import verify_extracted_document
from app.services.groq_extractor import extract_document_fields_with_groq
from app.utils.ocr_compat import save_ocr_verification
from app.utils.storage import download_file
from app.utils.supabase_client import get_supabase_client, safe_data

logger = logging.getLogger(__name__)
_ocr_engine = None


class OCRProcessingError(RuntimeError):
    """Raised when document loading or OCR execution fails."""


def get_ocr_engine():
    """Return the singleton PaddleOCR instance, loading it once if needed."""
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


def init_ocr_engine() -> bool:
    """Eagerly initialize PaddleOCR once at application startup."""
    try:
        get_ocr_engine()
        logger.info("PaddleOCR engine initialized at startup")
        return True
    except Exception as exc:
        logger.warning("PaddleOCR startup initialization deferred: %s", type(exc).__name__)
        return False


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
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return "\n".join(lines), round(avg_confidence, 4)


def _deskew_gray(gray: np.ndarray) -> np.ndarray:
    """Correct small skew angles based on foreground text orientation."""
    inverted = cv2.bitwise_not(gray)
    _, thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 50:
        return gray

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    elif angle > 45:
        angle = 90 - angle
    else:
        angle = -angle

    # Ignore negligible jitter or extreme 90-degree rotations.
    if abs(angle) < 0.5 or abs(angle) > 20.0:
        return gray

    height, width = gray.shape[:2]
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        gray,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def preprocess_image_bytes(image_bytes: bytes) -> bytes:
    """Apply grayscale, denoise, deskew, and adaptive thresholding via OpenCV."""
    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        return image_bytes

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    deskewed = _deskew_gray(denoised)
    thresholded = cv2.adaptiveThreshold(
        deskewed,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )
    bgr_output = cv2.cvtColor(thresholded, cv2.COLOR_GRAY2BGR)
    ok, encoded = cv2.imencode(".png", bgr_output)
    if not ok:
        raise OCRProcessingError("Failed to encode preprocessed image")
    return encoded.tobytes()


def _run_paddle_on_image_bytes(engine: Any, image_bytes: bytes) -> tuple[str, float]:
    processed_bytes = preprocess_image_bytes(image_bytes)
    suffix = ".png" if processed_bytes != image_bytes else ".jpg"
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(processed_bytes)
            temp_path = temp_file.name
        return _read_ocr_output(engine.ocr(temp_path, cls=True))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def extract_text_from_document(
    file_bytes: bytes,
    file_type: str,
    max_pdf_pages: int | None = 1,
) -> tuple[str, float]:
    """Load image (or first PDF page), preprocess with OpenCV, and run PaddleOCR."""
    if not file_bytes:
        raise OCRProcessingError("Document payload is empty")

    try:
        engine = get_ocr_engine()
        if file_type == "application/pdf":
            from pdf2image import convert_from_bytes

            convert_kwargs: dict[str, Any] = {"dpi": 200}
            if max_pdf_pages == 1:
                convert_kwargs["first_page"] = 1
                convert_kwargs["last_page"] = 1
            try:
                images = convert_from_bytes(file_bytes, **convert_kwargs)
            except TypeError:
                images = convert_from_bytes(file_bytes, dpi=200)

            if not images:
                raise OCRProcessingError("PDF contained no renderable pages")

            selected_images = images[:max_pdf_pages] if max_pdf_pages else images
            page_texts: list[str] = []
            page_confidences: list[float] = []
            for page in selected_images:
                buf = io.BytesIO()
                page.save(buf, format="JPEG")
                page_text, page_conf = _run_paddle_on_image_bytes(engine, buf.getvalue())
                if page_text:
                    page_texts.append(page_text)
                    page_confidences.append(page_conf)
            avg_conf = sum(page_confidences) / len(page_confidences) if page_confidences else 0.0
            return "\n".join(page_texts), round(avg_conf, 4)

        return _run_paddle_on_image_bytes(engine, file_bytes)
    except OCRProcessingError:
        raise
    except Exception as exc:
        logger.error("OCR extraction failed for type=%s (%s)", file_type, type(exc).__name__)
        raise OCRProcessingError(f"OCR extraction failed: {type(exc).__name__}") from exc


def _extract_text_from_file(file_bytes: bytes, file_type: str) -> tuple[str, float]:
    """Backward-compatible helper used by tests across all PDF pages."""
    return extract_text_from_document(file_bytes, file_type, max_pdf_pages=None)


def _sanitize_raw_text(raw_text: str, doc_type: str) -> str:
    """Mask any 12-digit Aadhaar numbers so only the last 4 digits are ever persisted."""
    if not raw_text:
        return ""
    if doc_type == "aadhaar":
        return re.sub(
            r"(?<!\d)\d{4}[ \t-]?\d{4}[ \t-]?(\d{4})(?!\d)",
            lambda match: f"XXXX-XXXX-{match.group(1)}",
            raw_text,
        )
    return raw_text


def process_document_ocr(
    document_id: str,
    user_id: str,
    storage_path: str,
    file_type: str,
    declared_type: str = "aadhaar",
) -> None:
    """Run download -> OCR -> Groq extraction -> verification -> DB save -> checklist sync."""
    supabase = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        supabase.table("documents").update({"status": "processing"}).eq(
            "id", document_id
        ).eq("user_id", user_id).execute()

        file_bytes = download_file(storage_path)
        ocr_text, ocr_confidence = extract_text_from_document(
            file_bytes, file_type, max_pdf_pages=1
        )
        sanitized_raw_text = _sanitize_raw_text(ocr_text, declared_type)
        extracted_fields = extract_document_fields_with_groq(sanitized_raw_text, declared_type)

        profile_response = supabase.table("user_profiles").select(
            "full_name,date_of_birth,gender,state,district,category,annual_income,land_holding_acres"
        ).eq("user_id", user_id).maybe_single().execute()
        profile = safe_data(profile_response) or {}
        verification = verify_extracted_document(
            declared_type,
            extracted_fields,
            profile,
            ocr_confidence,
        )

        verified_at = now_iso if verification["verification_status"] == "verified" else None
        save_ocr_verification(
            supabase,
            document_id,
            user_id,
            "completed",
            {
                "raw_text": sanitized_raw_text,
                "extracted_fields": extracted_fields,
                "ocr_confidence": verification["ocr_confidence"],
                "confidence_score": verification["confidence_score"],
                "detected_document_type": verification["detected_document_type"],
                "document_type_confidence": verification["document_type_confidence"],
                "verification_status": verification["verification_status"],
                "validation_summary": verification["validation_summary"],
                "mismatches": verification["mismatch_details"],
                "warnings": verification["warnings"],
                "processed_at": now_iso,
                "verified_at": verified_at,
            },
        )

        if verification["verification_status"] == "verified":
            try:
                mark_matching_checklist_tasks_complete(supabase, user_id, declared_type)
            except Exception:
                logger.error("Could not update matching checklist tasks for document_id=%s", document_id)
    except Exception as exc:
        logger.error(
            "Document verification failed for document_id=%s (%s)",
            document_id,
            type(exc).__name__,
        )
        try:
            save_ocr_verification(
                supabase,
                document_id,
                user_id,
                "failed",
                {
                    "raw_text": None,
                    "extracted_fields": {},
                    "ocr_confidence": 0.0,
                    "confidence_score": 0,
                    "detected_document_type": declared_type,
                    "document_type_confidence": 0,
                    "verification_status": "needs_review",
                    "validation_summary": "Verification could not be completed. Review the file or re-upload a clearer scan.",
                    "mismatches": [],
                    "warnings": ["OCR processing failed; no document details were confirmed."],
                    "processed_at": now_iso,
                    "verified_at": None,
                },
            )
        except Exception:
            logger.error("Could not save failure state for document_id=%s", document_id)

    try:
        from app.services.application_service import refresh_applications_for_document

        refresh_applications_for_document(supabase, user_id, document_id)
    except Exception:
        logger.error("Could not refresh application status for document_id=%s", document_id)
