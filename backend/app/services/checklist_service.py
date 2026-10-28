"""
AidFlow AI - Checklist Service
Creates practical checklist items for a selected scheme.
"""

import logging

from app.config import get_settings
from app.services.ai_service import generate_checklist

logger = logging.getLogger(__name__)


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
