"""Eligibility checks and history for the authenticated user."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.eligibility import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    EligibilityHistoryResponse,
)
from app.services.eligibility_engine import (
    ELIGIBLE_MATCH_THRESHOLD,
    evaluate_eligibility,
)
from app.utils.supabase_client import get_supabase_client

router = APIRouter()


@router.post("/check", response_model=EligibilityCheckResponse)
async def check_eligibility(data: EligibilityCheckRequest, user=Depends(get_current_user)):
    """Evaluate active scheme rules against the user's saved profile and form values."""
    supabase = get_supabase_client()

    profile_response = supabase.table("user_profiles").select(
        "full_name,state,district,occupation,category,annual_income,land_holding_acres,is_bpl,is_disabled"
    ).eq("user_id", user.id).maybe_single().execute()
    profile = profile_response.data or {}

    submitted_profile = data.model_dump(exclude_none=True)
    for field, value in submitted_profile.items():
        if isinstance(value, str) and not value.strip():
            continue
        profile[field] = value

    rules_response = supabase.table("scheme_rules").select(
        "scheme_id,rule_definition,schemes(id,name)"
    ).eq("is_active", True).execute()
    results = evaluate_eligibility(profile, rules_response.data or [])

    matched_count = sum(
        result["match_percentage"] >= ELIGIBLE_MATCH_THRESHOLD for result in results
    )
    check_response = supabase.table("eligibility_checks").insert({
        "user_id": user.id,
        "submitted_profile": profile,
        "matched_count": matched_count,
    }).execute()
    if not check_response.data:
        raise HTTPException(status_code=500, detail="Could not save eligibility check")

    check_id = check_response.data[0]["id"]
    result_rows = [
        {
            "check_id": check_id,
            "scheme_id": result["scheme_id"],
            "match_percentage": result["match_percentage"],
            "matched_rules": result["matched_rules"],
            "failed_rules": result["failed_rules"],
        }
        for result in results
    ]
    if result_rows:
        supabase.table("eligibility_results").insert(result_rows).execute()

    return EligibilityCheckResponse(
        check_id=check_id,
        matched_count=matched_count,
        results=results,
        checked_at=datetime.now(timezone.utc),
    )


@router.get("/history", response_model=EligibilityHistoryResponse)
async def get_eligibility_history(user=Depends(get_current_user)):
    """Return the latest eligibility checks belonging to the current user."""
    supabase = get_supabase_client()
    checks = supabase.table("eligibility_checks").select(
        "*, eligibility_results(*, schemes(name))"
    ).eq("user_id", user.id).order("checked_at", desc=True).limit(20).execute()

    formatted_checks = []
    for check in checks.data or []:
        results = [
            {
                "scheme_id": result["scheme_id"],
                "scheme_name": (result.get("schemes") or {}).get("name", "Unknown"),
                "match_percentage": result["match_percentage"],
                "matched_rules": result.get("matched_rules") or [],
                "failed_rules": result.get("failed_rules") or [],
            }
            for result in check.get("eligibility_results", [])
        ]
        formatted_checks.append({
            "check_id": check["id"],
            "matched_count": check.get("matched_count") or 0,
            "results": results,
            "checked_at": check["checked_at"],
        })

    return EligibilityHistoryResponse(checks=formatted_checks, total=len(formatted_checks))


@router.get("/history/{check_id}")
async def get_eligibility_detail(check_id: str, user=Depends(get_current_user)):
    """Return one saved check, scoped to the authenticated user."""
    supabase = get_supabase_client()
    check = supabase.table("eligibility_checks").select(
        "*, eligibility_results(*, schemes(name, description, benefits_summary))"
    ).eq("id", check_id).eq("user_id", user.id).maybe_single().execute()

    if not check.data:
        raise HTTPException(status_code=404, detail="Check not found")

    return check.data
