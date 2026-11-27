"""Groq LLM-backed assistant provider with deterministic fallback."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.config import get_settings
from app.services.ai.deterministic_provider import (
    DeterministicAssistantProvider,
    _scheme_cards,
)
from app.utils.groq_client import call_groq

logger = logging.getLogger(__name__)

_ALLOWED_INTERNAL_ROUTES = frozenset({
    "/dashboard",
    "/schemes",
    "/eligibility",
    "/documents",
    "/checklists",
    "/applications",
    "/analytics",
})


def _is_groq_configured() -> bool:
    key = (get_settings().GROQ_API_KEY or "").strip()
    if not key:
        return False
    lowered = key.lower()
    return not any(marker in lowered for marker in ("placeholder", "your-", "..."))


def _compact_context(context: dict[str, Any]) -> dict[str, Any]:
    """Build a compact JSON-serializable snapshot of the user's AidFlow state."""
    schemes = [
        {
            "id": str(s.get("id")),
            "name": s.get("name"),
            "category": s.get("category"),
            "ministry": s.get("ministry"),
            "description": s.get("description"),
            "benefits_summary": s.get("benefits_summary"),
            "eligibility_summary": s.get("eligibility_summary"),
            "deadline": str(s["deadline"]) if s.get("deadline") else None,
            "application_url": s.get("application_url"),
        }
        for s in (context.get("schemes") or [])
        if s.get("id") and s.get("name")
    ]
    eligibility_results = [
        {
            "scheme_id": str(r.get("scheme_id")),
            "scheme_name": (r.get("scheme") or {}).get("name"),
            "status": r.get("status"),
            "match_percentage": r.get("match_percentage"),
            "matched_rules": r.get("matched_rules") or [],
            "failed_rules": r.get("failed_rules") or [],
        }
        for r in (context.get("eligibility_results") or [])
    ]
    return {
        "profile": context.get("profile") or {},
        "dashboard_stats": context.get("dashboard_stats") or {},
        "eligibility_results": eligibility_results,
        "documents": context.get("documents") or [],
        "checklists": context.get("checklists") or [],
        "schemes": schemes,
    }


def _build_validated_cards(
    referenced_ids: list[Any], context: dict[str, Any]
) -> list[dict[str, Any]]:
    if not isinstance(referenced_ids, list) or not referenced_ids:
        return []
    result_by_id = {
        str(r.get("scheme_id")): r for r in (context.get("eligibility_results") or []) if r.get("scheme_id")
    }
    scheme_by_id = {
        str(s.get("id")): s for s in (context.get("schemes") or []) if s.get("id")
    }
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_id in referenced_ids[:4]:
        sid = str(raw_id)
        if sid in seen:
            continue
        if sid in result_by_id:
            rows.append(result_by_id[sid])
            seen.add(sid)
        elif sid in scheme_by_id:
            rows.append({"scheme": scheme_by_id[sid]})
            seen.add(sid)
    return _scheme_cards(rows)


def _validate_actions(raw_actions: Any, context: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(raw_actions, list):
        return []
    allowed_external_urls = {
        s.get("application_url")
        for s in (context.get("schemes") or [])
        if s.get("application_url")
    }
    validated: list[dict[str, Any]] = []
    for item in raw_actions[:3]:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        href = str(item.get("href") or "").strip()
        external = bool(item.get("external"))
        if not label or not href:
            continue
        if not external and href.split("?")[0] in _ALLOWED_INTERNAL_ROUTES:
            validated.append({"label": label[:60], "href": href, "external": False})
        elif external and href in allowed_external_urls:
            validated.append({"label": label[:60], "href": href, "external": True})
    return validated


class GroqAssistantProvider:
    """Answer user questions dynamically via Groq with grounded AidFlow context."""

    def __init__(self, fallback: DeterministicAssistantProvider | None = None):
        self.fallback = fallback or DeterministicAssistantProvider()

    def generate_response(self, question: str, context: dict[str, Any]) -> dict[str, Any]:
        if not _is_groq_configured():
            return self.fallback.generate_response(question, context)

        compact = _compact_context(context)
        history = [
            {"role": m.get("role"), "content": m.get("content")}
            for m in (context.get("history") or [])[-8:]
            if m.get("role") in ("user", "assistant") and m.get("content")
        ]

        system_prompt = (
            "You are AidFlow AI, a helpful, knowledgeable assistant for Indian government welfare schemes.\n"
            "You receive the user's saved AidFlow context (profile, eligibility check results, uploaded documents, "
            "checklists, dashboard stats, and active schemes in the database) plus recent conversation history.\n\n"
            "Guidelines:\n"
            "- Answer the user's actual question directly using natural, clear Markdown (headings, bullet points, bold text).\n"
            "- Use the saved AidFlow context accurately whenever personal status, eligibility percentages, documents, "
            "or checklists are relevant. Never fabricate saved user records or match percentages.\n"
            "- For general questions about schemes, application processes, documents, or follow-ups, explain clearly "
            "using your knowledge and the scheme records provided.\n"
            "- Respond ONLY with a valid JSON object matching this exact schema:\n"
            '  {"content": "<Markdown answer>", "referenced_scheme_ids": ["<scheme id from context>"], '
            '"actions": [{"label": "<short button text>", "href": "<route or url>", "external": false}]}\n'
            "- Only include scheme IDs that exist in the provided schemes/eligibility_results.\n"
            "- For internal actions, use only: /dashboard, /schemes, /eligibility, /documents, /checklists, /applications, /analytics.\n"
            "- For external actions, use only an exact application_url from the provided schemes."
        )

        user_payload = {
            "question": question,
            "recent_history": history,
            "aidflow_context": compact,
        }

        try:
            result = call_groq(
                system_prompt=system_prompt,
                user_prompt=json.dumps(user_payload, default=str),
                temperature=0.35,
                max_tokens=1500,
                json_mode=True,
                retries=1,
            )
            if not isinstance(result, dict) or result.get("parse_error"):
                raise ValueError("Groq assistant returned non-JSON or unparseable output")

            content = str(result.get("content") or "").strip()
            if not content:
                raise ValueError("Groq assistant returned empty content")

            return {
                "content": content,
                "scheme_cards": _build_validated_cards(
                    result.get("referenced_scheme_ids") or [], context
                ),
                "actions": _validate_actions(result.get("actions"), context),
            }
        except Exception as exc:
            logger.warning("Groq assistant failed (%s); falling back to deterministic provider", exc)
            return self.fallback.generate_response(question, context)
