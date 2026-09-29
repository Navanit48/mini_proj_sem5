"""
AidFlow AI - Documents Router
File upload, OCR processing, and document management.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from app.schemas.document import DocumentResponse, DocumentDetailResponse, DocumentListResponse
from app.utils.supabase_client import get_supabase_client
from app.utils.storage import upload_file, get_signed_url, delete_file
from app.dependencies import get_current_user
from app.services.ocr_service import process_document_ocr
from app.config import get_settings

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_category: str = "general",
    user=Depends(get_current_user),
):
    """Upload a document and trigger async OCR processing."""
    settings = get_settings()

    # Validate file type
    allowed_types = settings.ALLOWED_FILE_TYPES.split(",")
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")

    # Validate file size
    file_bytes = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_size:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    # Upload to Supabase Storage
    storage_path = upload_file(user.id, file_bytes, file.filename, file.content_type)

    # Save document record
    supabase = get_supabase_client()
    doc_data = {
        "user_id": user.id,
        "file_name": file.filename,
        "file_type": file.content_type,
        "storage_path": storage_path,
        "document_category": document_category,
        "status": "uploaded",
        "file_size_bytes": len(file_bytes),
    }
    response = supabase.table("documents").insert(doc_data).execute()
    doc = response.data[0]

    # Trigger async OCR processing
    background_tasks.add_task(process_document_ocr, doc["id"], storage_path, file.content_type)

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
    """Get document details with OCR results."""
    supabase = get_supabase_client()

    doc = supabase.table("documents").select("*").eq(
        "id", document_id
    ).eq("user_id", user.id).single().execute()

    if not doc.data:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.data["signed_url"] = get_signed_url(doc.data["storage_path"])

    # Get OCR results if available
    ocr = supabase.table("ocr_results").select("*").eq(
        "document_id", document_id
    ).single().execute()

    return DocumentDetailResponse(
        document=doc.data,
        ocr_result=ocr.data if ocr.data else None,
    )


@router.post("/{document_id}/ocr")
async def trigger_ocr(
    document_id: str,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    """Manually trigger OCR processing on a document."""
    supabase = get_supabase_client()

    doc = supabase.table("documents").select("*").eq(
        "id", document_id
    ).eq("user_id", user.id).single().execute()

    if not doc.data:
        raise HTTPException(status_code=404, detail="Document not found")

    background_tasks.add_task(
        process_document_ocr, document_id, doc.data["storage_path"], doc.data["file_type"]
    )

    return {"message": "OCR processing started", "document_id": document_id}


@router.delete("/{document_id}")
async def delete_document(document_id: str, user=Depends(get_current_user)):
    """Delete a document and its storage file."""
    supabase = get_supabase_client()

    doc = supabase.table("documents").select("*").eq(
        "id", document_id
    ).eq("user_id", user.id).single().execute()

    if not doc.data:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from storage
    delete_file(doc.data["storage_path"])

    # Delete OCR results
    supabase.table("ocr_results").delete().eq("document_id", document_id).execute()

    # Delete document record
    supabase.table("documents").delete().eq("id", document_id).execute()

    return {"message": "Document deleted"}
