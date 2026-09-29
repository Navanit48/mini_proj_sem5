"""
AidFlow AI - Eligibility Router
Evaluates user profile against scheme rules using the rule engine.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.schemas.eligibility import EligibilityCheckRequest, EligibilityCheckResponse, EligibilityHistoryResponse
from app.utils.supabase_client import get_supabase_client
from app.dependencies import get_current_user
from app.services.eligibility_engine import evaluate_eligibility
from datetime import datetime

router = APIRouter()


@router.post("/check", response_model=EligibilityCheckResponse)
async def check_eligibility(data: EligibilityCheckRequest, user=Depends(get_current_user)):
    """
    Submit user profile data and check eligibility against all active schemes.
    Returns matched schemes with match percentage and rule breakdown.
    """
    supabase = get_supabase_client()

    # Get all active scheme rules
    rules_response = supabase.table("scheme_rules").select(
        "*, schemes(id, name)"
    ).eq("is_active", True).execute()

    # Run eligibility engine
    results = evaluate_eligibility(data.model_dump(), rules_response.data)

    # Store the check in database
    check_data = {
        "user_id": user.id,
        "submitted_profile": data.model_dump(),
        "matched_count": len([r for r in results if r["match_percentage"] >= 50]),
    }
    check_response = supabase.table("eligibility_checks").insert(check_data).execute()
    check_id = check_response.data[0]["id"]

    # Store individual results
    for result in results:
        supabase.table("eligibility_results").insert({
            "check_id": check_id,
            "scheme_id": result["scheme_id"],
            "match_percentage": result["match_percentage"],
            "matched_rules": result["matched_rules"],
            "failed_rules": result["failed_rules"],
        }).execute()

    return EligibilityCheckResponse(
        check_id=check_id,
        matched_count=len([r for r in results if r["match_percentage"] >= 50]),
        results=results,
        checked_at=datetime.utcnow(),
    )


@router.get("/history", response_model=EligibilityHistoryResponse)
async def get_eligibility_history(user=Depends(get_current_user)):
    """Get past eligibility check results for the current user."""
    supabase = get_supabase_client()

    checks = supabase.table("eligibility_checks").select(
        "*, eligibility_results(*, schemes(name))"
    ).eq("user_id", user.id).order("checked_at", desc=True).limit(20).execute()

    formatted_checks = []
    for check in checks.data:
        results = []
        for r in check.get("eligibility_results", []):
            results.append({
                "scheme_id": r["scheme_id"],
                "scheme_name": r.get("schemes", {}).get("name", "Unknown"),
                "match_percentage": r["match_percentage"],
                "matched_rules": r.get("matched_rules", []),
                "failed_rules": r.get("failed_rules", []),
            })
        formatted_checks.append({
            "check_id": check["id"],
            "matched_count": check["matched_count"],
            "results": results,
            "checked_at": check["checked_at"],
        })

    return EligibilityHistoryResponse(
        checks=formatted_checks,
        total=len(formatted_checks),
    )


@router.get("/history/{check_id}")
async def get_eligibility_detail(check_id: str, user=Depends(get_current_user)):
    """Get detailed results for a specific eligibility check."""
    supabase = get_supabase_client()

    check = supabase.table("eligibility_checks").select(
        "*, eligibility_results(*, schemes(name, description, benefits_summary))"
    ).eq("id", check_id).eq("user_id", user.id).single().execute()

    if not check.data:
        raise HTTPException(status_code=404, detail="Check not found")

    return check.data
