"""
AidFlow AI - Documents Router
File upload and document management.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.schemas.document import DocumentResponse, DocumentDetailResponse, DocumentListResponse
from app.utils.supabase_client import get_supabase_client
from app.utils.storage import upload_file, get_signed_url, delete_file
from app.dependencies import get_current_user
from app.config import get_settings

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    document_category: str = "general",
    user=Depends(get_current_user),
):
    """Upload a PDF or JPEG document for the current user."""
    settings = get_settings()

    # Validate the declared MIME type and file signature.
    allowed_types = settings.ALLOWED_FILE_TYPES.split(",")
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")

    # Validate file size
    file_bytes = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_size:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    valid_signature = (
        file.content_type == "application/pdf" and file_bytes.startswith(b"%PDF-")
    ) or (
        file.content_type == "image/jpeg" and file_bytes.startswith(b"\xff\xd8\xff")
    )
    if not valid_signature:
        raise HTTPException(status_code=400, detail="File contents do not match the declared type")

    # Upload to Supabase Storage
    storage_path = upload_file(user.id, file_bytes, file.content_type)

    # Save document record
    supabase = get_supabase_client()
    doc_data = {
        "user_id": user.id,
        "file_name": file.filename or "document",
        "file_type": file.content_type,
        "storage_path": storage_path,
        "document_category": document_category,
        "status": "uploaded",
        "file_size_bytes": len(file_bytes),
    }
    try:
        response = supabase.table("documents").insert(doc_data).execute()
        if not response.data:
            raise RuntimeError("Document metadata insert returned no row")
        doc = response.data[0]
    except Exception:
        delete_file(storage_path)
        raise

    doc["signed_url"] = get_signed_url(storage_path)
    return doc


@router.get("", response_model=DocumentListResponse)
async def list_documents(user=Depends(get_current_user)):
    """List all documents for the current user."""
    supabase = get_supabase_client()
    response = supabase.table("documents").select("*").eq(
        "user_id", user.id
    ).order("uploaded_at", desc=True).execute()

    # Add signed URLs
    docs = []
    for doc in response.data:
        doc["signed_url"] = get_signed_url(doc["storage_path"])
        docs.append(doc)

    return DocumentListResponse(documents=docs, total=len(docs))


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: str, user=Depends(get_current_user)):
    """Get document details and a temporary viewing URL."""
    supabase = get_supabase_client()

    response = supabase.table("documents").select("*").eq(
        "id", document_id
    ).eq("user_id", user.id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = response.data[0]
    doc["signed_url"] = get_signed_url(doc["storage_path"])
    return DocumentDetailResponse(document=doc)


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

    # Delete document record
    supabase.table("documents").delete().eq("id", document_id).eq(
        "user_id", user.id
    ).execute()

    return {"message": "Document deleted"}
