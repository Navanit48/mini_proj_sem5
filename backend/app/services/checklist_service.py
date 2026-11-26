"""
AidFlow AI - Checklist Service
Creates practical checklist items for a selected scheme.
"""

import logging
import re
from datetime import datetime, timezone

from app.config import get_settings
from app.services.ai_service import generate_checklist

logger = logging.getLogger(__name__)

DOC_TYPE_CHECKLIST_KEYWORDS: dict[str, tuple[str, ...]] = {
    "aadhaar": ("aadhaar", "aadhar", "identity card", "id proof"),
    "income_certificate": ("income certificate", "income proof", "annual income"),
    "caste_certificate": ("caste certificate", "category certificate", "caste"),
    "bank_passbook": ("bank passbook", "passbook", "bank account", "ifsc"),
    "photo": ("passport photo", "passport-size photo", "photograph"),
}


def mark_matching_checklist_tasks_complete(supabase, user_id: str, doc_type: str) -> int:
    """Mark incomplete checklist items matching a verified doc_type as complete."""
    keywords = DOC_TYPE_CHECKLIST_KEYWORDS.get(doc_type, ())
    if not keywords:
        return 0

    cl_response = supabase.table("checklists").select("id").eq("user_id", user_id).execute()
    checklist_ids = [row["id"] for row in (cl_response.data or []) if row.get("id")]
    if not checklist_ids:
        return 0

    now_iso = datetime.now(timezone.utc).isoformat()
    completed_count = 0

    for checklist_id in checklist_ids:
        items_response = supabase.table("checklist_items").select(
            "id,title,description,is_completed"
        ).eq("checklist_id", checklist_id).execute()
        items = items_response.data or []
        if not items:
            continue

        matched_ids: list[str] = []
        for item in items:
            if item.get("is_completed"):
                continue
            haystack = f"{item.get('title') or ''} {item.get('description') or ''}".lower()
            if any(re.search(rf"\b{re.escape(kw)}\b", haystack) for kw in keywords):
                matched_ids.append(item["id"])

        for item_id in matched_ids:
            supabase.table("checklist_items").update({
                "is_completed": True,
                "completed_at": now_iso,
            }).eq("id", item_id).eq("checklist_id", checklist_id).execute()
            completed_count += 1

        if matched_ids:
            all_complete = all(
                item.get("is_completed") or item.get("id") in matched_ids
                for item in items
            )
            if all_complete:
                supabase.table("checklists").update({
                    "status": "completed",
                    "updated_at": now_iso,
                }).eq("id", checklist_id).eq("user_id", user_id).execute()

    return completed_count


def _default_checklist(scheme_data: dict) -> list[dict]:
    return [
        {
            "title": "Review scheme requirements",
            "description": "Read the official eligibility and application guidelines.",
            "due_date_offset_days": 1,
        },
        {
            "title": "Gather required documents",
            "description": "Collect identity, address, and scheme-specific documents.",
            "due_date_offset_days": 3,
        },
        {
            "title": "Submit the application",
            "description": f"Apply through the official portal: {scheme_data.get('application_url') or 'scheme portal'}.",
            "due_date_offset_days": 7,
        },
    ]


async def generate_checklist_items(scheme_data: dict) -> list[dict]:
    """Generate scheme tasks, with a reliable default when AI is unavailable."""
    name = scheme_data.get("name", "Unknown Scheme")
    summary = f"""
    Benefits: {scheme_data.get('benefits_summary', '')}
    Eligibility: {scheme_data.get('eligibility_summary', '')}
    Category: {scheme_data.get('category', '')}
    """

    if not get_settings().GROQ_API_KEY.strip():
        return _default_checklist(scheme_data)

    try:
        items = generate_checklist(name, summary)
    except Exception:
        logger.exception("Checklist generation failed for scheme %s", name)
        items = []

    valid_items = [
        item for item in items
        if isinstance(item, dict) and isinstance(item.get("title"), str) and item["title"].strip()
    ] if isinstance(items, list) else []
    return valid_items if valid_items else _default_checklist(scheme_data)
