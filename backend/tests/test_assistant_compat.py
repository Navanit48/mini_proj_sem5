import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import httpx

from app.dependencies import get_current_user
from app.main import app


class _LegacyAssistantQuery:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.op = "select"
        self.columns = "*"
        self.filters = []
        self.payload = None
        self.single = False
        self.ordering = None
        self.limit_count = None

    def select(self, columns="*", **_kwargs):
        self.op = "select"
        self.columns = columns
        return self

    def insert(self, payload):
        self.op = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.op = "update"
        self.payload = payload
        return self

    def delete(self):
        self.op = "delete"
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def order(self, key, desc=False):
        self.ordering = (key, desc)
        return self

    def limit(self, value):
        self.limit_count = value
        return self

    def maybe_single(self):
        self.single = True
        return self

    def execute(self):
        if self.table_name == "assistant_messages":
            raise Exception(
                "{'message': \"Could not find the table 'public.assistant_messages' in the schema cache\", 'code': 'PGRST205'}"
            )
        if self.table_name == "assistant_conversations":
            if self.op == "select" and "title" in self.columns:
                raise Exception("{'message': 'column assistant_conversations.title does not exist', 'code': '42703'}")
            if self.op in {"insert", "update"} and "title" in (self.payload or {}):
                raise Exception(
                    "{'message': \"Could not find the 'title' column of 'assistant_conversations' in the schema cache\", 'code': 'PGRST204'}"
                )

        rows = self.client.rows.setdefault(self.table_name, [])
        if self.op == "insert":
            now = datetime.now(timezone.utc).isoformat()
            row = {"id": str(uuid4()), "created_at": now, "updated_at": now, **self.payload}
            rows.append(row)
            return SimpleNamespace(data=[row])

        filtered = [row for row in rows if all(row.get(k) == v for k, v in self.filters)]
        if self.op == "update":
            for row in filtered:
                row.update(self.payload)
            return SimpleNamespace(data=filtered)
        if self.op == "delete":
            self.client.rows[self.table_name] = [row for row in rows if row not in filtered]
            return SimpleNamespace(data=filtered)
        if self.ordering:
            key, desc = self.ordering
            filtered.sort(key=lambda row: row.get(key) or "", reverse=desc)
        if self.limit_count is not None:
            filtered = filtered[:self.limit_count]
        return SimpleNamespace(data=(filtered[0] if filtered else None) if self.single else list(filtered))


class _LegacyAssistantSupabase:
    def __init__(self, user_id):
        self.rows = {
            "user_profiles": [{"user_id": user_id, "full_name": "Asha Rao", "state": "Bihar"}],
            "schemes": [],
            "eligibility_checks": [],
            "documents": [],
            "checklists": [],
            "assistant_conversations": [],
        }

    def table(self, name):
        return _LegacyAssistantQuery(self, name)


class AssistantCompatTests(unittest.IsolatedAsyncioTestCase):
    async def test_assistant_routes_work_with_legacy_messages_jsonb_schema(self):
        user_id = str(uuid4())
        supabase = _LegacyAssistantSupabase(user_id)
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)
        try:
            with (
                patch("app.routers.assistant.get_supabase_client", return_value=supabase),
                patch("app.services.ai.groq_provider._is_groq_configured", return_value=False),
            ):
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    created = await client.post("/api/v1/assistant/conversations", json={})
                    self.assertEqual(created.status_code, 201, created.text)
                    conv_id = created.json()["conversation_id"]

                    sent = await client.post(
                        f"/api/v1/assistant/conversations/{conv_id}/messages",
                        json={"content": "What should I do next?"},
                    )
                    self.assertEqual(sent.status_code, 200, sent.text)
                    self.assertEqual(sent.json()["user_message"]["content"], "What should I do next?")
                    self.assertEqual(sent.json()["assistant_message"]["role"], "assistant")

                    listing = await client.get("/api/v1/assistant/conversations")
                    self.assertEqual(listing.status_code, 200, listing.text)
                    self.assertEqual(listing.json()["total"], 1)
                    self.assertEqual(listing.json()["conversations"][0]["title"], "What should I do next?")

                    opened = await client.get(f"/api/v1/assistant/conversations/{conv_id}")
                    self.assertEqual(opened.status_code, 200, opened.text)
                    self.assertEqual(len(opened.json()["messages"]), 2)

                    deleted = await client.delete(f"/api/v1/assistant/conversations/{conv_id}")
                    self.assertEqual(deleted.status_code, 204, deleted.text)
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
