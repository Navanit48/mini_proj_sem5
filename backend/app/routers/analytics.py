"""
AidFlow AI - Analytics Router
Provides dashboard data and aggregated statistics.
"""

import logging

from fastapi import APIRouter, Depends
from app.utils.supabase_client import get_supabase_client
from app.dependencies import get_current_user, require_admin
from app.services.ai_recommendation import get_recommendation_provider

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def get_dashboard_stats(user=Depends(get_current_user)):
    """Get personal dashboard statistics for the user."""
    supabase = get_supabase_client()

    profile_response = supabase.table("user_profiles").select("*").eq(
        "user_id", user.id
    ).maybe_single().execute()
    profile = profile_response.data or {}
    completion_fields = (
        "full_name",
        "phone",
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
    checklist_total = len(checklist_items.data)
    checklist_completed = sum(item.get("is_completed") is True for item in checklist_items.data)

    documents = supabase.table("documents").select(
        "document_category", count="exact"
    ).eq("user_id", user.id).execute()
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
            documents.data or [],
        )
    except Exception:
        logger.exception("Could not build dashboard AI insights")
        ai_insights = []

    return {
        "profile_completion": round(completed_profile_fields / len(completion_fields) * 100),
        "eligible_schemes": eligible_schemes_count,
        "uploaded_documents": documents.count or 0,
        "ai_insights": ai_insights,
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
    for p in popular.data:
        name = p.get("schemes", {}).get("name", "Unknown")
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
