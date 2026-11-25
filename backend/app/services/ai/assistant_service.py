"""Loads owned AidFlow data and persists provider-neutral assistant conversations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException

from app.services.ai.deterministic_provider import DeterministicAssistantProvider
from app.services.ai.provider import AssistantProvider
from app.services.ai_recommendation import get_recommendation_provider
from app.utils.ocr_compat import is_missing_column_error
from app.utils.supabase_client import safe_data


def _derive_title(messages: list[dict[str, Any]] | None) -> str:
    """Build a conversation title from the first user message when no title column exists."""
    for message in messages or []:
        if message.get("role") == "user" and str(message.get("content") or "").strip():
            text = str(message["content"]).strip()
            return text[:117] + ("..." if len(text) > 120 else "")
    return "New conversation"


def _normalize_legacy_messages(
    messages: list[dict[str, Any]] | None,
    fallback_timestamp: Any,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, message in enumerate(messages or []):
        role = message.get("role")
        if role not in ("user", "assistant"):
            continue
        normalized.append({
            "id": str(message.get("id") or f"msg-{index}"),
            "role": role,
            "content": str(message.get("content") or ""),
            "created_at": message.get("created_at") or fallback_timestamp,
            "metadata": message.get("metadata") or {},
        })
    return normalized


class AssistantService:
    def __init__(self, supabase: Any, provider: AssistantProvider | None = None):
        self.supabase = supabase
        self.provider = provider or DeterministicAssistantProvider()

    def list_conversations(self, user_id: str) -> list[dict[str, Any]]:
        try:
            response = self.supabase.table("assistant_conversations").select(
                "id,title,created_at,updated_at"
            ).eq("user_id", user_id).order("updated_at", desc=True).limit(50).execute()
            return response.data or []
        except Exception as error:
            if not is_missing_column_error(error):
                raise
            response = self.supabase.table("assistant_conversations").select(
                "id,messages,created_at,updated_at"
            ).eq("user_id", user_id).order("updated_at", desc=True).limit(50).execute()
            return [
                {
                    "id": row["id"],
                    "title": row.get("title") or _derive_title(row.get("messages")),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in (response.data or [])
            ]

    def create_conversation(self, user_id: str, title: str | None = None) -> dict[str, Any]:
        clean_title = title.strip()[:120] if title and title.strip() else "New conversation"
        try:
            response = self.supabase.table("assistant_conversations").insert({
                "user_id": user_id,
                "title": clean_title,
            }).execute()
        except Exception as error:
            if not is_missing_column_error(error):
                raise
            response = self.supabase.table("assistant_conversations").insert({
                "user_id": user_id,
                "messages": [],
            }).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Could not create assistant conversation")
        row = dict(response.data[0])
        row.setdefault("title", clean_title)
        return row

    def get_conversation(self, user_id: str, conversation_id: str) -> list[dict[str, Any]]:
        conversation = self._owned_conversation(user_id, conversation_id)
        try:
            response = self.supabase.table("assistant_messages").select(
                "id,role,content,metadata,created_at"
            ).eq("conversation_id", conversation_id).eq("user_id", user_id).order("created_at").execute()
            return response.data or []
        except Exception as error:
            if not is_missing_column_error(error):
                raise
            return _normalize_legacy_messages(
                conversation.get("messages"),
                conversation.get("created_at") or datetime.now(timezone.utc).isoformat(),
            )

    def delete_conversation(self, user_id: str, conversation_id: str) -> None:
        self._owned_conversation(user_id, conversation_id)
        self.supabase.table("assistant_conversations").delete().eq(
            "id", conversation_id
        ).eq("user_id", user_id).execute()

    def send_message(self, user_id: str, conversation_id: str, question: str) -> dict[str, Any]:
        conversation = self._owned_conversation(user_id, conversation_id)
        clean_question = question.strip()
        generated = self.provider.generate_response(clean_question, self.load_context(user_id))
        metadata = {
            "scheme_cards": generated.get("scheme_cards", []),
            "actions": generated.get("actions", []),
        }
        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            user_row = self._insert_message(user_id, conversation_id, "user", clean_question, {})
            assistant_row = self._insert_message(
                user_id, conversation_id, "assistant", generated["content"], metadata
            )
            updates: dict[str, Any] = {"updated_at": now_iso}
            if conversation.get("title") == "New conversation":
                updates["title"] = clean_question[:117] + ("..." if len(clean_question) > 120 else "")
            self.supabase.table("assistant_conversations").update(updates).eq(
                "id", conversation_id
            ).eq("user_id", user_id).execute()
            return {"user_message": user_row, "assistant_message": assistant_row}
        except Exception as error:
            if not is_missing_column_error(error):
                raise
            existing_messages = _normalize_legacy_messages(
                conversation.get("messages"),
                conversation.get("created_at") or now_iso,
            )
            user_row = {
                "id": str(uuid4()),
                "role": "user",
                "content": clean_question,
                "created_at": now_iso,
                "metadata": {},
            }
            assistant_row = {
                "id": str(uuid4()),
                "role": "assistant",
                "content": generated["content"],
                "created_at": now_iso,
                "metadata": metadata,
            }
            self.supabase.table("assistant_conversations").update({
                "messages": [*existing_messages, user_row, assistant_row],
                "updated_at": now_iso,
            }).eq("id", conversation_id).eq("user_id", user_id).execute()
            return {"user_message": user_row, "assistant_message": assistant_row}

    def load_context(self, user_id: str) -> dict[str, Any]:
        profile_response = self.supabase.table("user_profiles").select("*").eq(
            "user_id", user_id
        ).maybe_single().execute()
        profile = safe_data(profile_response) or {}
        scheme_response = self.supabase.table("schemes").select("*").eq(
            "is_active", True
        ).execute()
        schemes = scheme_response.data or []
        scheme_by_id = {str(scheme["id"]): scheme for scheme in schemes}

        checks_response = self.supabase.table("eligibility_checks").select(
            "id,submitted_profile,matched_count,checked_at,eligibility_results(*,schemes(*))"
        ).eq("user_id", user_id).order("checked_at", desc=True).limit(10).execute()
        checks = checks_response.data or []
        latest_check_id = str(checks[0].get("id")) if checks else None
        eligibility_results = []
        recent_checked_schemes = []
        for check in checks:
            for result in check.get("eligibility_results") or []:
                scheme = result.get("schemes") or scheme_by_id.get(str(result.get("scheme_id")), {})
                if scheme:
                    recent_checked_schemes.append(scheme)
                if str(check.get("id")) != latest_check_id:
                    continue
                row = {
                    "scheme_id": str(result.get("scheme_id")),
                    "scheme": scheme,
                    "match_percentage": float(result.get("match_percentage") or 0),
                    "matched_rules": result.get("matched_rules") or [],
                    "failed_rules": result.get("failed_rules") or [],
                    "checked_at": check.get("checked_at"),
                }
                row["status"] = (
                    "Eligible" if row["match_percentage"] >= 70 else
                    "Partially Eligible" if row["match_percentage"] >= 40 else
                    "Not Eligible"
                )
                eligibility_results.append(row)

        documents_response = self.supabase.table("documents").select(
            "file_name,document_category,status,uploaded_at"
        ).eq("user_id", user_id).order("uploaded_at", desc=True).execute()
        documents = documents_response.data or []
        checklist_response = self.supabase.table("checklists").select(
            "id,scheme_id,status,checklist_items(id,title,is_completed),schemes(name)"
        ).eq("user_id", user_id).execute()
        checklists = []
        raw_checklists = checklist_response.data or []
        for checklist in raw_checklists:
            items = checklist.get("checklist_items") or []
            pending = [item.get("title") for item in items if not item.get("is_completed") and item.get("title")]
            checklists.append({
                "scheme_id": checklist.get("scheme_id"),
                "scheme_name": (checklist.get("schemes") or {}).get("name") or "Scheme",
                "total_count": len(items),
                "completed_count": len(items) - len(pending),
                "pending_count": len(pending),
                "pending_titles": pending,
                "status": checklist.get("status"),
            })

        if eligibility_results:
            ranked = get_recommendation_provider().build_eligibility_recommendations(
                profile,
                [
                    {
                        **item,
                        "scheme_name": item["scheme"].get("name", "Scheme"),
                    }
                    for item in eligibility_results
                ],
                scheme_by_id,
                raw_checklists,
                documents,
            )["results"]
            score_by_id = {
                str(item["scheme_id"]): (
                    item.get("ai_recommendation") or {}
                ).get("priority_score")
                for item in ranked
            }
            eligibility_results.sort(
                key=lambda item: (
                    score_by_id.get(str(item["scheme_id"])) or 0,
                    item["match_percentage"],
                ),
                reverse=True,
            )
            for item in eligibility_results:
                item["priority_score"] = score_by_id.get(str(item["scheme_id"]))

        # Keep these aggregates consistent with /analytics/dashboard.
        fields = ("full_name", "gender", "state", "district", "occupation", "annual_income", "category")
        profile_completion = round(
            sum(profile.get(field) is not None and profile.get(field) != "" for field in fields)
            / len(fields) * 100
        )
        dashboard_stats = {
            "profile_completion": profile_completion,
            "eligible_schemes": sum(item["status"] == "Eligible" for item in eligibility_results),
            "uploaded_documents": len(documents),
            "checklist_total": sum(item["total_count"] for item in checklists),
            "checklist_completed": sum(item["completed_count"] for item in checklists),
        }
        return {
            "profile": profile,
            "schemes": schemes,
            "eligibility_results": eligibility_results,
            "recent_checked_schemes": recent_checked_schemes[:12],
            "documents": documents,
            "checklists": checklists,
            "dashboard_stats": dashboard_stats,
        }

    def _owned_conversation(self, user_id: str, conversation_id: str) -> dict[str, Any]:
        try:
            UUID(conversation_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=404, detail="Conversation not found")
        try:
            response = self.supabase.table("assistant_conversations").select(
                "id,user_id,title,created_at,updated_at"
            ).eq("id", conversation_id).eq("user_id", user_id).maybe_single().execute()
        except Exception as error:
            if not is_missing_column_error(error):
                raise
            response = self.supabase.table("assistant_conversations").select(
                "id,user_id,messages,created_at,updated_at"
            ).eq("id", conversation_id).eq("user_id", user_id).maybe_single().execute()
        data = safe_data(response)
        if not data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return data

    def _insert_message(
        self, user_id: str, conversation_id: str, role: str, content: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        response = self.supabase.table("assistant_messages").insert({
            "user_id": user_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "metadata": metadata,
        }).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Could not save assistant message")
        return response.data[0]
