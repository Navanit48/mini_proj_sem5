"""
AidFlow AI - Analytics Router
Provides dashboard data and aggregated statistics.
"""

from fastapi import APIRouter, Depends
from app.utils.supabase_client import get_supabase_client
from app.dependencies import get_current_user, require_admin

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(user=Depends(get_current_user)):
    """Get personal dashboard statistics for the user."""
    supabase = get_supabase_client()

    # 1. Total Matched Schemes
    eligibility = supabase.table("eligibility_checks").select(
        "matched_count"
    ).eq("user_id", user.id).order("checked_at", desc=True).limit(1).execute()

    matched_schemes_count = 0
    if eligibility.data:
        matched_schemes_count = eligibility.data[0]["matched_count"]

    # 2. Pending Checklist Items
    pending_items = supabase.table("checklist_items").select(
        "id, is_completed, checklists!inner(user_id)"
    ).eq("checklists.user_id", user.id).eq("is_completed", False).execute()
    pending_tasks_count = len(pending_items.data)

    # 3. Total Documents Uploaded
    documents = supabase.table("documents").select(
        "id", count="exact"
    ).eq("user_id", user.id).execute()
    documents_count = documents.count or 0

    return {
        "matched_schemes": matched_schemes_count,
        "pending_tasks": pending_tasks_count,
        "uploaded_documents": documents_count,
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
