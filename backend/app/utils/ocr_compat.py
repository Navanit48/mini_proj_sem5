"""Schema-compatibility helpers for reading and writing OCR verification results."""

from __future__ import annotations

from typing import Any

from app.utils.supabase_client import safe_data

DOCUMENT_VERIFICATION_FIELDS = (
    "verification_status",
    "validation_summary",
    "mismatches",
    "warnings",
)


def is_missing_column_error(error: Exception) -> bool:
    """Return True when PostgREST reports a missing column/table or stale schema cache."""
    text = str(error)
    return (
        "PGRST204" in text
        or "PGRST205" in text
        or "42703" in text
        or "42P01" in text
        or "does not exist" in text
        or "schema cache" in text
    )


def normalize_ocr_result(
    row: dict[str, Any] | None,
    doc: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Normalize legacy and migrated ocr_results rows into the API response shape."""
    if not row:
        return None
    normalized = dict(row)
    confidence = normalized.get("confidence_score")
    if confidence is None:
        confidence = normalized.get("confidence")
    normalized["confidence_score"] = float(confidence or 0.0)
    normalized["extracted_fields"] = normalized.get("extracted_fields") or {}

    for field in DOCUMENT_VERIFICATION_FIELDS:
        if normalized.get(field) is None and doc and doc.get(field) is not None:
            normalized[field] = doc.get(field)

    if normalized.get("mismatches") is None:
        normalized["mismatches"] = []
    if normalized.get("warnings") is None:
        normalized["warnings"] = []
    return normalized


def fetch_ocr_results_by_document_ids(
    supabase,
    document_ids: list[str],
    docs_by_id: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Batch-fetch and normalize ocr_results rows keyed by document_id."""
    if not document_ids:
        return {}
    response = supabase.table("ocr_results").select("*").in_(
        "document_id", document_ids
    ).execute()
    results: dict[str, dict[str, Any]] = {}
    for row in response.data or []:
        doc_id = row.get("document_id")
        if doc_id:
            normalized = normalize_ocr_result(row, (docs_by_id or {}).get(doc_id))
            if normalized is not None:
                results[doc_id] = normalized
    return results


def fetch_ocr_result_for_document(
    supabase,
    document_id: str,
    doc: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Fetch and normalize a single ocr_results row by document_id."""
    response = supabase.table("ocr_results").select("*").eq(
        "document_id", document_id
    ).maybe_single().execute()
    return normalize_ocr_result(safe_data(response), doc)


def save_ocr_verification(
    supabase,
    document_id: str,
    user_id: str,
    doc_status: str,
    payload: dict[str, Any],
) -> None:
    """Persist OCR verification to ocr_results and documents across schema versions."""
    full_ocr_payload = {
        "document_id": document_id,
        "raw_text": payload.get("raw_text"),
        "extracted_fields": payload.get("extracted_fields") or {},
        "confidence_score": payload.get("confidence_score", 0),
        "detected_document_type": payload.get("detected_document_type"),
        "document_type_confidence": payload.get("document_type_confidence", 0),
        "verification_status": payload.get("verification_status"),
        "validation_summary": payload.get("validation_summary"),
        "mismatches": payload.get("mismatches") or [],
        "warnings": payload.get("warnings") or [],
        "processed_at": payload.get("processed_at"),
    }
    doc_update: dict[str, Any] = {"status": doc_status}

    try:
        supabase.table("ocr_results").upsert(
            full_ocr_payload, on_conflict="document_id"
        ).execute()
    except Exception as error:
        if not is_missing_column_error(error):
            raise
        legacy_ocr_payload = {
            "document_id": document_id,
            "raw_text": payload.get("raw_text"),
            "extracted_fields": payload.get("extracted_fields") or {},
            "confidence": payload.get("confidence_score", 0),
            "processed_at": payload.get("processed_at"),
        }
        supabase.table("ocr_results").upsert(
            legacy_ocr_payload, on_conflict="document_id"
        ).execute()
        for field in DOCUMENT_VERIFICATION_FIELDS:
            if field in payload:
                doc_update[field] = payload[field]

    try:
        supabase.table("documents").update(doc_update).eq(
            "id", document_id
        ).eq("user_id", user_id).execute()
    except Exception as error:
        if doc_update == {"status": doc_status} or not is_missing_column_error(error):
            raise
        supabase.table("documents").update({"status": doc_status}).eq(
            "id", document_id
        ).eq("user_id", user_id).execute()
