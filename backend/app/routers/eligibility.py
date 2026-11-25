"""Eligibility checks and history for the authenticated user."""

from datetime import datetime, timezone
import logging

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
from app.services.ai_recommendation import get_recommendation_provider
from app.utils.supabase_client import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)


def _load_recommendation_context(supabase, user_id: str):
    try:
        checklists = supabase.table("checklists").select(
            "scheme_id,status,checklist_items(id,is_completed)"
        ).eq("user_id", user_id).execute()
        checklist_data = checklists.data or []
    except Exception:
        logger.exception("Could not load checklist context for recommendations")
        checklist_data = []
    try:
        documents = supabase.table("documents").select(
            "document_category"
        ).eq("user_id", user_id).execute()
        document_data = documents.data or []
    except Exception:
        logger.exception("Could not load document context for recommendations")
        document_data = []
    return checklist_data, document_data


def _build_ai_result(profile, results, schemes, checklists, documents):
    try:
        return get_recommendation_provider().build_eligibility_recommendations(
            profile, results, schemes, checklists, documents
        )
    except Exception:
        logger.exception("Deterministic eligibility recommendations failed")
        return {
            "profile_strength": 0,
            "eligible_schemes": [],
            "near_misses": [],
            "evaluated_count": len(results),
            "results": results,
        }


def _format_saved_check(check, checklists, documents):
    saved_results = []
    schemes = {}
    for result in check.get("eligibility_results") or []:
        scheme = result.get("schemes") or {}
        scheme_id = str(result["scheme_id"])
        scheme_name = scheme.get("name", "Unknown")
        saved_results.append({
            "scheme_id": scheme_id,
            "scheme_name": scheme_name,
            "match_percentage": result.get("match_percentage") or 0,
            "matched_rules": result.get("matched_rules") or [],
            "failed_rules": result.get("failed_rules") or [],
        })
        schemes[scheme_id] = scheme

    ai_result = _build_ai_result(
        check.get("submitted_profile") or {},
        saved_results,
        schemes,
        checklists,
        documents,
    )
    return {
        "check_id": check["id"],
        "matched_count": check.get("matched_count") or 0,
        "results": ai_result["results"],
        "checked_at": check["checked_at"],
        "ai_summary": {
            "profile_strength": ai_result["profile_strength"],
            "eligible_schemes": ai_result["eligible_schemes"],
            "near_misses": ai_result["near_misses"],
            "evaluated_count": ai_result["evaluated_count"],
        },
    }


@router.post("/check", response_model=EligibilityCheckResponse)
async def check_eligibility(data: EligibilityCheckRequest, user=Depends(get_current_user)):
    """Evaluate active scheme rules against the user's saved profile and form values."""
    supabase = get_supabase_client()

    profile_response = supabase.table("user_profiles").select(
        "full_name,date_of_birth,gender,state,district,occupation,category,annual_income,land_holding_acres,is_bpl,is_disabled"
    ).eq("user_id", user.id).maybe_single().execute()
    profile = profile_response.data or {}

    submitted_profile = data.model_dump(exclude_none=True)
    for field, value in submitted_profile.items():
        if isinstance(value, str) and not value.strip():
            continue
        profile[field] = value

    rules_response = supabase.table("scheme_rules").select(
        "scheme_id,rule_definition,schemes(id,name,benefits_summary,deadline,application_url,category)"
    ).eq("is_active", True).execute()
    results = evaluate_eligibility(profile, rules_response.data or [])
    scheme_data = {
        str(rule["scheme_id"]): {
            **(rule.get("schemes") or {}),
            "rule_definition": rule.get("rule_definition") or {},
        }
        for rule in (rules_response.data or [])
    }
    checklists, documents = _load_recommendation_context(supabase, user.id)
    ai_result = _build_ai_result(profile, results, scheme_data, checklists, documents)

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
        results=ai_result["results"],
        checked_at=datetime.now(timezone.utc),
        ai_summary={
            "profile_strength": ai_result["profile_strength"],
            "eligible_schemes": ai_result["eligible_schemes"],
            "near_misses": ai_result["near_misses"],
            "evaluated_count": ai_result["evaluated_count"],
        },
    )


@router.get("/history", response_model=EligibilityHistoryResponse)
async def get_eligibility_history(user=Depends(get_current_user)):
    """Return the latest eligibility checks belonging to the current user."""
    supabase = get_supabase_client()
    checks = supabase.table("eligibility_checks").select(
        "*, eligibility_results(*, schemes(name,benefits_summary,deadline,application_url,category))"
    ).eq("user_id", user.id).order("checked_at", desc=True).limit(20).execute()

    checklists, documents = _load_recommendation_context(supabase, user.id)
    formatted_checks = [
        _format_saved_check(check, checklists, documents)
        for check in (checks.data or [])
    ]

    return EligibilityHistoryResponse(checks=formatted_checks, total=len(formatted_checks))


@router.get("/history/{check_id}")
async def get_eligibility_detail(check_id: str, user=Depends(get_current_user)):
    """Return one saved check, scoped to the authenticated user."""
    supabase = get_supabase_client()
    check = supabase.table("eligibility_checks").select(
        "*, eligibility_results(*, schemes(name,description,benefits_summary,deadline,application_url,category))"
    ).eq("id", check_id).eq("user_id", user.id).maybe_single().execute()

    if not check.data:
        raise HTTPException(status_code=404, detail="Check not found")

    checklists, documents = _load_recommendation_context(supabase, user.id)
    return _format_saved_check(check.data, checklists, documents)
