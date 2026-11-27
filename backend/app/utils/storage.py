"""
AidFlow AI - Storage Utility
Handles file operations with Supabase Storage.
"""

import logging
import uuid

from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
BUCKET_NAME = "documents"


def upload_file(user_id: str, file_bytes: bytes, content_type: str) -> str:
    """
    Upload a file to Supabase Storage.
    
    Returns:
        The storage path of the uploaded file.
    """
    supabase = get_supabase_client()
    
    # Store each user's documents in their own folder with a server-generated name.
    ext_map = {
        "application/pdf": ".pdf",
        "image/png": ".png",
        "image/jpeg": ".jpg",
    }
    ext = ext_map.get(content_type, ".jpg")
    unique_name = f"{uuid.uuid4()}{ext}"
    storage_path = f"{user_id}/{unique_name}"

    supabase.storage.from_(BUCKET_NAME).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": content_type, "upsert": "false"},
    )

    return storage_path


def get_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """Generate a signed URL for a stored file, returning '' if missing."""
    if not storage_path:
        return ""
    try:
        supabase = get_supabase_client()
        response = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            path=storage_path,
            expires_in=expires_in,
        )
        return response.get("signedURL") or response.get("signedUrl", "")
    except Exception as exc:
        logger.warning("Could not create signed URL for %s: %s", storage_path, exc)
        return ""


def delete_file(storage_path: str) -> bool:
    """Delete a file from Supabase Storage, ignoring already-missing files."""
    if not storage_path:
        return False
    try:
        supabase = get_supabase_client()
        supabase.storage.from_(BUCKET_NAME).remove([storage_path])
        return True
    except Exception as exc:
        logger.warning("Could not delete storage file %s: %s", storage_path, exc)
        return False


def download_file(storage_path: str) -> bytes:
    """Download file bytes from Supabase Storage."""
    supabase = get_supabase_client()
    response = supabase.storage.from_(BUCKET_NAME).download(storage_path)
    return response
