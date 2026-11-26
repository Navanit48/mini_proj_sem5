"""
AidFlow AI - Analytics Router
Provides dashboard data and aggregated statistics.
"""

import logging

from fastapi import APIRouter, Depends
from app.utils.ocr_compat import fetch_ocr_results_by_document_ids
from app.utils.supabase_client import get_supabase_client, safe_data
from app.dependencies import get_current_user, require_admin
from app.services.ai_recommendation import get_recommendation_provider
from app.services.application_service import list_applications

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def get_dashboard_stats(user=Depends(get_current_user)):
    """Get personal dashboard statistics for the user."""
    supabase = get_supabase_client()

    profile_response = supabase.table("user_profiles").select("*").eq(
        "user_id", user.id
    ).maybe_single().execute()
    profile = safe_data(profile_response) or {}
    completion_fields = (
        "full_name",
        "gender",
        "state",
        "district",
        "occupation",
        "annual_income",
        "category",
    )
    completed_profile_fields = sum(
        profile.get(field) is not None and profile.get(field) != ""
        for field in completion_fields
    )

    eligibility = supabase.table("eligibility_checks").select(
        "matched_count,submitted_profile,eligibility_results(*,schemes(name,benefits_summary,deadline,application_url,category))"
    ).eq("user_id", user.id).order("checked_at", desc=True).limit(1).execute()

    eligible_schemes_count = (eligibility.data[0]["matched_count"] or 0) if eligibility.data else 0
    latest_check = eligibility.data[0] if eligibility.data else {}
    ai_profile = latest_check.get("submitted_profile") or profile
    ai_results = []
    ai_schemes = {}
    for result in latest_check.get("eligibility_results") or []:
        scheme = result.get("schemes") or {}
        scheme_id = str(result["scheme_id"])
        ai_results.append({
            "scheme_id": scheme_id,
            "scheme_name": scheme.get("name", "Unknown"),
            "match_percentage": result.get("match_percentage") or 0,
            "matched_rules": result.get("matched_rules") or [],
            "failed_rules": result.get("failed_rules") or [],
        })
        ai_schemes[scheme_id] = scheme

    checklist_items = supabase.table("checklist_items").select(
        "id, is_completed, checklists!inner(user_id)"
    ).eq("checklists.user_id", user.id).execute()
    checklist_rows = checklist_items.data or []
    checklist_total = len(checklist_rows)
    checklist_completed = sum(item.get("is_completed") is True for item in checklist_rows)

    documents = supabase.table("documents").select(
        "id,document_category,status,verification_status", count="exact"
    ).eq("user_id", user.id).execute()
    document_rows = documents.data or []
    docs_by_id = {document["id"]: document for document in document_rows if document.get("id")}
    verification_by_id = fetch_ocr_results_by_document_ids(
        supabase, list(docs_by_id.keys()), docs_by_id
    )
    verification_rows = list(verification_by_id.values())
    verification_summary = {
        "verified": sum(
            row.get("verification_status") in {"verified", "preliminary_match"}
            for row in verification_rows
        ),
        "preliminary_match": sum(
            row.get("verification_status") in {"verified", "preliminary_match"}
            for row in verification_rows
        ),
        "mismatch": sum(row.get("verification_status") == "mismatch" for row in verification_rows),
        "needs_review": sum(row.get("verification_status") == "needs_review" for row in verification_rows),
        "unreadable": sum(row.get("verification_status") == "unreadable" for row in verification_rows),
        "processing": sum(
            document.get("status") in {"pending", "uploaded", "processing"}
            or document.get("id") not in verification_by_id
            for document in document_rows
        ),
    }
    pending_documents = sum(
        document.get("status") in {"pending", "uploaded", "processing", "failed"}
        or (document.get("status") == "completed" and document.get("id") not in verification_by_id)
        or verification_by_id.get(document.get("id"), {}).get("verification_status") in {"pending", "mismatch", "needs_review", "unreadable"}
        for document in document_rows
    )
    try:
        checklists = supabase.table("checklists").select(
            "scheme_id,status,checklist_items(id,is_completed),schemes(name)"
        ).eq("user_id", user.id).execute()
        checklist_data = checklists.data or []
        for checklist in checklist_data:
            checklist["scheme_name"] = (checklist.get("schemes") or {}).get("name")
        ai_insights = get_recommendation_provider().build_dashboard_insights(
            ai_profile,
            ai_results,
            ai_schemes,
            checklist_data,
            document_rows,
        )
    except Exception:
        logger.exception("Could not build dashboard AI insights")
        ai_insights = []

    try:
        recent_applications = list_applications(supabase, user.id)[:3]
    except Exception:
        logger.exception("Could not load application data for dashboard")
        recent_applications = []

    return {
        "profile_completion": round(completed_profile_fields / len(completion_fields) * 100),
        "eligible_schemes": eligible_schemes_count,
        "uploaded_documents": documents.count if documents.count is not None else len(document_rows),
        "ai_insights": ai_insights,
        "recent_applications": recent_applications,
        "verification_summary": verification_summary,
        "pending_documents": pending_documents,
        "application_progress": recent_applications[0]["progress"] if recent_applications else 0,
        "checklist_progress": {
            "completed": checklist_completed,
            "total": checklist_total,
            "percentage": round(checklist_completed / checklist_total * 100) if checklist_total else 0,
        },
    }


@router.get("/admin")
async def get_admin_analytics(admin=Depends(require_admin)):
    """Get platform-wide analytics (Admin only)."""
    supabase = get_supabase_client()

    # Total Users
    users = supabase.table("user_profiles").select("id", count="exact").execute()

    # Total Schemes
    schemes = supabase.table("schemes").select("id", count="exact").eq("is_active", True).execute()

    # Total Eligibility Checks
    checks = supabase.table("eligibility_checks").select("id", count="exact").execute()

    # Popular Schemes (most matched)
    popular = supabase.table("eligibility_results").select(
        "scheme_id, schemes(name)"
    ).gte("match_percentage", 50).execute()

    scheme_counts = {}
    for p in popular.data or []:
        name = (p.get("schemes") or {}).get("name", "Unknown")
        scheme_counts[name] = scheme_counts.get(name, 0) + 1

    top_schemes = sorted(
        [{"name": k, "count": v} for k, v in scheme_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:5]

    return {
        "total_users": users.count or 0,
        "active_schemes": schemes.count or 0,
        "total_checks_run": checks.count or 0,
        "top_matched_schemes": top_schemes,
    }
