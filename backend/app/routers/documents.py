"""
AidFlow AI - Documents Router
File upload, listing, verification status, and deletion.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.dependencies import get_current_user
from app.schemas.document import (
    ALLOWED_DOC_TYPES,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
)
from app.services.ocr_service import process_document_ocr
from app.utils.ocr_compat import (
    fetch_ocr_result_for_document,
    fetch_ocr_results_by_document_ids,
    is_missing_column_error,
    normalize_document_row,
)
from app.utils.storage import delete_file, get_signed_url, upload_file
from app.utils.supabase_client import get_supabase_client, safe_data

router = APIRouter()

DOC_TYPE_ALIASES = {
    "passport_photo": "photo",
}


def _resolve_doc_type(doc_type: str | None, document_category: str | None) -> str:
    raw_value = (doc_type or document_category or "").strip().lower()
    resolved = DOC_TYPE_ALIASES.get(raw_value, raw_value)
    if resolved not in ALLOWED_DOC_TYPES:
        allowed = ", ".join(ALLOWED_DOC_TYPES)
        raise HTTPException(
            status_code=422,
            detail=f"Invalid doc_type '{raw_value}'. Allowed types: {allowed}",
        )
    return resolved


def _validate_upload_file(file: UploadFile, file_bytes: bytes) -> str:
    settings = get_settings()
    content_type = (file.content_type or "").lower().strip()
    if content_type == "image/jpg":
        content_type = "image/jpeg"

    allowed_types = {t.strip().lower() for t in settings.ALLOWED_FILE_TYPES.split(",") if t.strip()}
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed. Use JPG, PNG, or PDF.")

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(file_bytes) > max_size:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    valid_signature = (
        (content_type == "application/pdf" and file_bytes.startswith(b"%PDF-"))
        or (content_type == "image/jpeg" and file_bytes.startswith(b"\xff\xd8\xff"))
        or (content_type == "image/png" and file_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
    )
    if not valid_signature:
        raise HTTPException(status_code=400, detail="File contents do not match the declared type")

    return content_type


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str | None = Form(default=None),
    document_category: str | None = Form(default=None),
    user=Depends(get_current_user),
):
    """Upload a JPG, PNG, or PDF document (max 5 MB) with status pending."""
    resolved_doc_type = _resolve_doc_type(doc_type, document_category)
    file_bytes = await file.read()
    content_type = _validate_upload_file(file, file_bytes)

    storage_path = upload_file(user.id, file_bytes, content_type)
    supabase = get_supabase_client()
    doc_data = {
        "user_id": user.id,
        "file_name": file.filename or "document",
        "file_type": content_type,
        "storage_path": storage_path,
        "doc_type": resolved_doc_type,
        "document_category": resolved_doc_type,
        "status": "pending",
        "verification_status": "pending",
        "file_size_bytes": len(file_bytes),
    }

    try:
        try:
            response = supabase.table("documents").insert(doc_data).execute()
        except Exception as error:
            if not is_missing_column_error(error) and "23514" not in str(error) and "check constraint" not in str(error):
                raise
            legacy_doc_data = {
                "user_id": user.id,
                "file_name": file.filename or "document",
                "file_type": content_type,
                "storage_path": storage_path,
                "document_category": resolved_doc_type,
                "status": "uploaded",
                "file_size_bytes": len(file_bytes),
            }
            response = supabase.table("documents").insert(legacy_doc_data).execute()

        if not response.data:
            raise RuntimeError("Document metadata insert returned no row")
        doc = response.data[0]
    except Exception:
        delete_file(storage_path)
        raise

    doc["signed_url"] = get_signed_url(storage_path)
    return normalize_document_row(doc, None)


@router.get("", response_model=DocumentListResponse)
async def list_documents(user=Depends(get_current_user)):
    """List all documents for the current user."""
    supabase = get_supabase_client()
    response = supabase.table("documents").select("*").eq(
        "user_id", user.id
    ).order("uploaded_at", desc=True).execute()

    raw_documents = response.data or []
    docs_by_id = {doc["id"]: doc for doc in raw_documents if doc.get("id")}
    verification_by_document = fetch_ocr_results_by_document_ids(
        supabase, list(docs_by_id.keys()), docs_by_id
    )

    docs = []
    for doc in raw_documents:
        doc["signed_url"] = get_signed_url(doc["storage_path"])
        docs.append(normalize_document_row(doc, verification_by_document.get(doc["id"])))

    return DocumentListResponse(documents=docs, total=len(docs))


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: str, user=Depends(get_current_user)):
    """Get document details, verification state, and a signed viewing URL."""
    supabase = get_supabase_client()
    response = supabase.table("documents").select("*").eq(
        "id", document_id
    ).eq("user_id", user.id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = response.data[0]
    doc["signed_url"] = get_signed_url(doc["storage_path"])
    verification = fetch_ocr_result_for_document(supabase, document_id, doc)
    normalized = normalize_document_row(doc, verification)
    return DocumentDetailResponse(document=normalized, verification=verification)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str, user=Depends(get_current_user)):
    """Pollable status endpoint for document OCR and verification."""
    supabase = get_supabase_client()
    response = supabase.table("documents").select("*").eq(
        "id", document_id
    ).eq("user_id", user.id).maybe_single().execute()
    doc = safe_data(response)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    verification = fetch_ocr_result_for_document(supabase, document_id, doc)
    normalized = normalize_document_row(doc, verification)
    normalized["signed_url"] = get_signed_url(doc["storage_path"])
    return DocumentStatusResponse(**normalized)


@router.post("/{document_id}/verify", status_code=202)
async def verify_document_again(
    document_id: str,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    """Queue OCR, Groq extraction, and profile verification in the background."""
    supabase = get_supabase_client()
    response = supabase.table("documents").select("*").eq(
        "id", document_id
    ).eq("user_id", user.id).maybe_single().execute()
    doc = safe_data(response)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        supabase.table("documents").update({
            "status": "processing",
            "verification_status": "pending",
        }).eq("id", document_id).eq("user_id", user.id).execute()
    except Exception as error:
        if (
            not is_missing_column_error(error)
            and "23514" not in str(error)
            and "check constraint" not in str(error)
        ):
            raise
        supabase.table("documents").update({"status": "processing"}).eq(
            "id", document_id
        ).eq("user_id", user.id).execute()

    doc_type = doc.get("doc_type") or doc.get("document_category") or "aadhaar"
    background_tasks.add_task(
        process_document_ocr,
        document_id,
        user.id,
        doc["storage_path"],
        doc["file_type"],
        doc_type,
    )
    return {
        "document_id": document_id,
        "status": "processing",
        "verification_status": doc.get("verification_status") or "pending",
    }


@router.delete("/{document_id}")
async def delete_document(document_id: str, user=Depends(get_current_user)):
    """Delete a document and its storage file."""
    supabase = get_supabase_client()
    response = supabase.table("documents").select("*").eq(
        "id", document_id
    ).eq("user_id", user.id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = response.data[0]
    delete_file(doc["storage_path"])
    supabase.table("documents").delete().eq("id", document_id).eq(
        "user_id", user.id
    ).execute()
    return {"message": "Document deleted"}
