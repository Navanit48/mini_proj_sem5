"""Build and track AidFlow application packages without contacting government systems."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.schemas.user import UserProfileUpdate
from app.utils.ocr_compat import fetch_ocr_results_by_document_ids
from app.utils.supabase_client import safe_data

PROFILE_FIELDS = (
    "full_name", "date_of_birth", "gender", "state", "district", "occupation",
    "category", "annual_income", "land_holding_acres", "is_bpl", "is_disabled",
)

INTERNAL_STAGES = {
    "submitted": ("under_review", 25, "AidFlow is checking the saved application package."),
    "under_review": ("ai_document_verification", 55, "AidFlow is reviewing the attached documents using preliminary OCR checks."),
}


def _load_profile(supabase, user_id: str) -> dict[str, Any]:
    response = supabase.table("user_profiles").select(",".join(PROFILE_FIELDS)).eq(
        "user_id", user_id
    ).maybe_single().execute()
    data = safe_data(response)
    if not data:
        raise HTTPException(status_code=404, detail="User profile not found")
    return data


def _load_scheme(supabase, scheme_id: str) -> dict[str, Any]:
    response = supabase.table("schemes").select(
        "id,name,ministry,category,description,benefits_summary,eligibility_summary,application_url"
    ).eq("id", scheme_id).eq("is_active", True).maybe_single().execute()
    data = safe_data(response)
    if not data:
        raise HTTPException(status_code=404, detail="Active scheme not found")
    return data


def _load_eligibility(supabase, user_id: str, scheme_id: str, check_id: str | None = None) -> dict[str, Any]:
    if check_id:
        check_response = supabase.table("eligibility_checks").select(
            "id,checked_at,submitted_profile"
        ).eq("id", check_id).eq("user_id", user_id).maybe_single().execute()
        check = safe_data(check_response)
        if not check:
            raise HTTPException(status_code=404, detail="Eligibility check not found")
    else:
        checks_response = supabase.table("eligibility_checks").select(
            "id,checked_at,submitted_profile"
        ).eq("user_id", user_id).order("checked_at", desc=True).limit(10).execute()
        check = next(iter(checks_response.data or []), None)

    if not check:
        return {}
    result_response = supabase.table("eligibility_results").select(
        "scheme_id,match_percentage,matched_rules,failed_rules"
    ).eq("check_id", check["id"]).eq("scheme_id", scheme_id).maybe_single().execute()
    result = safe_data(result_response)
    if not result:
        if check_id:
            raise HTTPException(status_code=400, detail="The selected eligibility check has no result for this scheme")
        return {}
    percentage = float(result.get("match_percentage") or 0)
    status = "Eligible" if percentage >= 70 else "Partially Eligible" if percentage >= 40 else "Not Eligible"
    return {
        "check_id": check["id"],
        "checked_at": check.get("checked_at"),
        "status": status,
        "match_percentage": percentage,
        "matched_rules": result.get("matched_rules") or [],
        "failed_rules": result.get("failed_rules") or [],
        "notice": "AidFlow rule-based guidance only; this is not an official eligibility decision.",
    }


def _load_owned_documents(supabase, user_id: str, document_ids: list[str]) -> list[dict[str, Any]]:
    if not document_ids:
        return []
    response = supabase.table("documents").select(
        "id,user_id,file_name,file_type,document_category,status,file_size_bytes,uploaded_at,"
        "verification_status,validation_summary,mismatches,warnings"
    ).eq("user_id", user_id).in_("id", document_ids).execute()
    documents = response.data or []
    if len({doc["id"] for doc in documents}) != len(set(document_ids)):
        raise HTTPException(status_code=400, detail="One or more selected documents are unavailable")
    return documents


def _verification_by_document(
    supabase,
    document_ids: list[str],
    docs_by_id: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    return fetch_ocr_results_by_document_ids(supabase, document_ids, docs_by_id)


def create_application_preview(
    supabase, user_id: str, scheme_id: str, eligibility_check_id: str | None = None
) -> dict[str, Any]:
    profile = _load_profile(supabase, user_id)
    scheme = _load_scheme(supabase, scheme_id)
    eligibility = _load_eligibility(supabase, user_id, scheme_id, eligibility_check_id)
    documents_response = supabase.table("documents").select(
        "id,user_id,file_name,file_type,document_category,status,file_size_bytes,uploaded_at,"
        "verification_status,validation_summary,mismatches,warnings"
    ).eq("user_id", user_id).order("uploaded_at", desc=True).execute()
    documents = documents_response.data or []
    docs_by_id = {doc["id"]: doc for doc in documents if doc.get("id")}
    verifications = _verification_by_document(supabase, list(docs_by_id.keys()), docs_by_id)
    for doc in documents:
        doc["verification"] = verifications.get(doc["id"])
    missing_profile_fields = [
        field for field in PROFILE_FIELDS
        if profile.get(field) is None or profile.get(field) == ""
    ]
    return {
        "scheme": scheme,
        "profile": profile,
        "eligibility": eligibility,
        "documents": documents,
        "missing_profile_fields": missing_profile_fields,
        "notice": "This review creates an AidFlow application package. It does not submit information to a government portal.",
    }


def submit_application(
    supabase,
    user_id: str,
    scheme_id: str,
    profile_overrides: dict[str, Any],
    document_ids: list[str],
    eligibility_check_id: str | None,
) -> dict[str, Any]:
    preview = create_application_preview(supabase, user_id, scheme_id, eligibility_check_id)
    try:
        validated_overrides = UserProfileUpdate.model_validate(profile_overrides).model_dump(
            mode="json", exclude_unset=True
        )
    except Exception as error:
        raise HTTPException(status_code=422, detail="Application profile contains invalid fields") from error
    profile_snapshot = {**preview["profile"], **validated_overrides}
    profile_snapshot = {field: profile_snapshot.get(field) for field in PROFILE_FIELDS}
    documents = _load_owned_documents(supabase, user_id, document_ids)
    docs_by_id = {doc["id"]: doc for doc in documents if doc.get("id")}
    verification = _verification_by_document(supabase, list(docs_by_id.keys()), docs_by_id)
    document_snapshots = []
    for document in documents:
        result = verification.get(document["id"], {})
        document_snapshots.append({
            "id": document["id"],
            "file_name": document["file_name"],
            "file_type": document["file_type"],
            "document_category": document.get("document_category"),
            "status": document["status"],
            "uploaded_at": document.get("uploaded_at"),
            "verification_status": result.get("verification_status"),
            "confidence_score": result.get("confidence_score"),
            "extracted_fields": result.get("extracted_fields") or {},
            "validation_summary": result.get("validation_summary"),
            "mismatches": result.get("mismatches") or [],
        })

    eligibility = preview["eligibility"]
    application_code = f"AF{datetime.now(timezone.utc).year}{secrets.token_hex(3).upper()}"
    inserted = supabase.table("applications").insert({
        "application_code": application_code,
        "user_id": user_id,
        "scheme_id": scheme_id,
        "eligibility_check_id": eligibility.get("check_id"),
        "status": "submitted",
        "profile_snapshot": profile_snapshot,
        "eligibility_snapshot": eligibility,
    }).execute()
    if not inserted.data:
        raise HTTPException(status_code=500, detail="Could not create application package")
    application = inserted.data[0]

    try:
        if document_snapshots:
            supabase.table("application_documents").insert([
                {
                    "application_id": application["id"],
                    "document_id": doc["id"],
                    "document_snapshot": doc,
                }
                for doc in document_snapshots
            ]).execute()
        supabase.table("application_events").insert({
            "application_id": application["id"],
            "status": "submitted",
            "description": "Your application package was saved in AidFlow for tracking.",
            "progress": 10,
        }).execute()
    except Exception:
        supabase.table("applications").delete().eq("id", application["id"]).eq(
            "user_id", user_id
        ).execute()
        raise
    return application


def advance_application(supabase, application_id: str, user_id: str) -> bool:
    """Advance one AidFlow-owned workflow stage when its prerequisites are met."""
    app_response = supabase.table("applications").select(
        "id,user_id,status"
    ).eq("id", application_id).eq("user_id", user_id).maybe_single().execute()
    application = safe_data(app_response)
    if not application:
        return False
    status = application["status"]
    if status in INTERNAL_STAGES:
        next_status, progress, description = INTERNAL_STAGES[status]
    elif status == "ai_document_verification":
        links = supabase.table("application_documents").select(
            "document_id"
        ).eq("application_id", application_id).execute()
        document_ids = [row["document_id"] for row in (links.data or []) if row.get("document_id")]
        docs = _load_owned_documents(supabase, user_id, document_ids)
        if any(doc.get("status") in {"uploaded", "processing"} for doc in docs):
            return False
        next_status = "ready_for_government_submission"
        progress = 75
        description = (
            "AidFlow finished its preliminary document checks. Review any warnings and submit the package through the official scheme channel."
            if docs else
            "The AidFlow package is assembled. No documents were attached; confirm the scheme's official document requirements before external submission."
        )
    else:
        return False

    updated = supabase.table("applications").update({
        "status": next_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", application_id).eq("user_id", user_id).eq("status", status).execute()
    if not updated.data:
        return False
    existing_event = supabase.table("application_events").select("id").eq(
        "application_id", application_id
    ).eq("status", next_status).maybe_single().execute()
    if not safe_data(existing_event):
        supabase.table("application_events").insert({
            "application_id": application_id,
            "status": next_status,
            "description": description,
            "progress": progress,
        }).execute()
    return True


def progress_application_workflow(supabase, application_id: str, user_id: str) -> None:
    for _ in range(3):
        if not advance_application(supabase, application_id, user_id):
            break


def _serialize_application(supabase, application: dict[str, Any], user_id: str) -> dict[str, Any]:
    links_response = supabase.table("application_documents").select(
        "document_id,document_snapshot"
    ).eq("application_id", application["id"]).execute()
    links = links_response.data or []
    document_ids = [row["document_id"] for row in links if row.get("document_id")]
    live_documents = {
        doc["id"]: doc for doc in _load_owned_documents(supabase, user_id, document_ids)
    } if document_ids else {}
    verifications = _verification_by_document(supabase, document_ids)
    documents = []
    for link in links:
        snapshot = link.get("document_snapshot") or {}
        doc_id = link.get("document_id")
        current = live_documents.get(doc_id, {})
        result = verifications.get(doc_id, {})
        documents.append({
            "id": doc_id or snapshot.get("id", "deleted-document"),
            "document_id": doc_id,
            "file_name": snapshot.get("file_name", "Document"),
            "document_category": snapshot.get("document_category"),
            "status": current.get("status", snapshot.get("status", "deleted")),
            "verification_status": result.get("verification_status", snapshot.get("verification_status")),
            "confidence_score": result.get("confidence_score", snapshot.get("confidence_score")),
            "extracted_fields": result.get("extracted_fields", snapshot.get("extracted_fields", {})),
            "uploaded_at": snapshot.get("uploaded_at"),
        })

    scheme_response = supabase.table("schemes").select("id,name").eq(
        "id", application["scheme_id"]
    ).maybe_single().execute()
    scheme_data = safe_data(scheme_response)
    events_response = supabase.table("application_events").select(
        "status,description,progress,occurred_at"
    ).eq("application_id", application["id"]).order("occurred_at").execute()
    events = sorted(
        events_response.data or [],
        key=lambda event: (event.get("progress", 0), str(event.get("occurred_at") or "")),
    )
    progress = events[-1]["progress"] if events else 0
    return {
        **application,
        "scheme_name": (scheme_data or {}).get("name", "Scheme"),
        "progress": progress,
        "documents": documents,
        "timeline": events,
        "external_stages": [
            {
                "status": "not_started",
                "title": "Government review",
                "description": "This step begins only after you submit the package through the official government channel.",
                "occurred_at": None,
                "progress": 0,
            },
            {
                "status": "not_started",
                "title": "Government decision (approved or rejected)",
                "description": "AidFlow does not receive or simulate an official decision.",
                "occurred_at": None,
                "progress": 0,
            },
        ],
    }


def list_applications(supabase, user_id: str) -> list[dict[str, Any]]:
    response = supabase.table("applications").select("*").eq(
        "user_id", user_id
    ).order("submitted_at", desc=True).limit(30).execute()
    applications = response.data or []
    serialized = []
    for application in applications:
        progress_application_workflow(supabase, application["id"], user_id)
        refreshed = supabase.table("applications").select("*").eq(
            "id", application["id"]
        ).eq("user_id", user_id).maybe_single().execute()
        refreshed_data = safe_data(refreshed)
        if refreshed_data:
            serialized.append(_serialize_application(supabase, refreshed_data, user_id))
    return serialized


def get_application(supabase, user_id: str, application_id: str) -> dict[str, Any]:
    progress_application_workflow(supabase, application_id, user_id)
    response = supabase.table("applications").select("*").eq(
        "id", application_id
    ).eq("user_id", user_id).maybe_single().execute()
    data = safe_data(response)
    if not data:
        raise HTTPException(status_code=404, detail="Application not found")
    return _serialize_application(supabase, data, user_id)


def refresh_applications_for_document(supabase, user_id: str, document_id: str) -> None:
    links = supabase.table("application_documents").select(
        "application_id"
    ).eq("document_id", document_id).execute()
    for link in links.data or []:
        progress_application_workflow(supabase, link["application_id"], user_id)
