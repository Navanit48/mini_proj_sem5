"""AidFlow application package preview, submission, and status tracking."""

from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user
from app.schemas.application import (
    ApplicationListResponse,
    ApplicationPreviewRequest,
    ApplicationPreviewResponse,
    ApplicationResponse,
    ApplicationSubmitRequest,
)
from app.services.application_service import (
    create_application_preview,
    get_application,
    list_applications,
    submit_application,
)
from app.utils.supabase_client import get_supabase_client

router = APIRouter()


@router.post("/preview", response_model=ApplicationPreviewResponse)
async def preview_application(data: ApplicationPreviewRequest, user=Depends(get_current_user)):
    return create_application_preview(
        get_supabase_client(), user.id, data.scheme_id, data.eligibility_check_id
    )


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationSubmitRequest,
    user=Depends(get_current_user),
):
    supabase = get_supabase_client()
    application = submit_application(
        supabase,
        user.id,
        data.scheme_id,
        data.profile_overrides,
        data.document_ids,
        data.eligibility_check_id,
    )
    return get_application(supabase, user.id, application["id"])


@router.get("", response_model=ApplicationListResponse)
async def list_user_applications(user=Depends(get_current_user)):
    applications = list_applications(get_supabase_client(), user.id)
    return {"applications": applications, "total": len(applications)}


@router.get("/{application_id}", response_model=ApplicationResponse)
async def application_detail(application_id: str, user=Depends(get_current_user)):
    return get_application(get_supabase_client(), user.id, application_id)
