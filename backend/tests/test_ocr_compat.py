import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import httpx

from app.dependencies import get_current_user
from app.main import app
from app.utils.ocr_compat import save_ocr_verification


class _LegacyQuery:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.op = "select"
        self.filters = []
        self.membership = []
        self.payload = None
        self.single = False

    def select(self, *_args, **_kwargs):
        self.op = "select"
        return self

    def upsert(self, payload, **_kwargs):
        self.op = "upsert"
        self.payload = payload
        return self

    def update(self, payload):
        self.op = "update"
        self.payload = payload
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def in_(self, key, values):
        self.membership.append((key, values))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args):
        return self

    def maybe_single(self):
        self.single = True
        return self

    def execute(self):
        rows = self.client.rows.setdefault(self.table_name, [])
        if self.op == "upsert":
            if self.table_name == "ocr_results" and "confidence_score" in self.payload:
                raise Exception(
                    "{'message': \"Could not find the 'confidence_score' column of 'ocr_results' in the schema cache\", 'code': 'PGRST204'}"
                )
            existing = next(
                (row for row in rows if row.get("document_id") == self.payload.get("document_id")),
                None,
            )
            if existing:
                existing.update(self.payload)
                return SimpleNamespace(data=[existing])
            row = {"id": str(uuid4()), **self.payload}
            rows.append(row)
            return SimpleNamespace(data=[row])

        filtered = [
            row for row in rows
            if all(row.get(k) == v for k, v in self.filters)
            and all(row.get(k) in vals for k, vals in self.membership)
        ]
        if self.op == "update":
            for row in filtered:
                row.update(self.payload)
            return SimpleNamespace(data=filtered)

        count = len(filtered)
        data = (filtered[0] if filtered else None) if self.single else list(filtered)
        return SimpleNamespace(data=data, count=count)


class _LegacySupabase:
    def __init__(self, user_id, doc_id):
        now = datetime.now(timezone.utc).isoformat()
        self.rows = {
            "user_profiles": [{"user_id": user_id, "full_name": "Asha Rao"}],
            "eligibility_checks": [],
            "checklist_items": [],
            "checklists": [],
            "applications": [],
            "documents": [{
                "id": doc_id,
                "user_id": user_id,
                "file_name": "income.pdf",
                "file_type": "application/pdf",
                "storage_path": f"{user_id}/income.pdf",
                "document_category": "income_certificate",
                "status": "failed",
                "file_size_bytes": 1024,
                "uploaded_at": now,
                "verification_status": "unreadable",
                "validation_summary": "Preliminary verification could not be completed.",
                "mismatches": [],
                "warnings": ["OCR unavailable"],
            }],
            "ocr_results": [{
                "id": str(uuid4()),
                "document_id": doc_id,
                "raw_text": None,
                "confidence": 0.0,
                "extracted_fields": {},
                "processed_at": now,
            }],
        }

    def table(self, name):
        return _LegacyQuery(self, name)


class OCRCompatTests(unittest.IsolatedAsyncioTestCase):
    async def test_documents_and_dashboard_work_with_legacy_ocr_results_schema(self):
        user_id = str(uuid4())
        doc_id = str(uuid4())
        supabase = _LegacySupabase(user_id, doc_id)
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)
        try:
            with (
                patch("app.routers.documents.get_supabase_client", return_value=supabase),
                patch("app.routers.documents.get_signed_url", return_value="https://example.invalid/signed"),
                patch("app.routers.analytics.get_supabase_client", return_value=supabase),
            ):
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    listing = await client.get("/api/v1/documents")
                    self.assertEqual(listing.status_code, 200, listing.text)
                    docs = listing.json()["documents"]
                    self.assertEqual(len(docs), 1)
                    self.assertEqual(docs[0]["verification"]["confidence_score"], 0.0)
                    self.assertEqual(docs[0]["verification"]["verification_status"], "unreadable")

                    detail = await client.get(f"/api/v1/documents/{doc_id}")
                    self.assertEqual(detail.status_code, 200, detail.text)
                    self.assertEqual(detail.json()["verification"]["confidence_score"], 0.0)

                    dashboard = await client.get("/api/v1/analytics/dashboard")
                    self.assertEqual(dashboard.status_code, 200, dashboard.text)
                    self.assertEqual(dashboard.json()["verification_summary"]["unreadable"], 1)
        finally:
            app.dependency_overrides.clear()

    def test_save_ocr_verification_falls_back_to_legacy_columns(self):
        user_id = str(uuid4())
        doc_id = str(uuid4())
        supabase = _LegacySupabase(user_id, doc_id)
        save_ocr_verification(
            supabase,
            doc_id,
            user_id,
            "completed",
            {
                "raw_text": None,
                "extracted_fields": {"full_name": "Asha Rao"},
                "confidence_score": 88.5,
                "verification_status": "preliminary_match",
                "validation_summary": "Matched.",
                "mismatches": [],
                "warnings": [],
                "processed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        self.assertEqual(supabase.rows["ocr_results"][0]["confidence"], 88.5)
        self.assertEqual(supabase.rows["documents"][0]["status"], "completed")
        self.assertEqual(supabase.rows["documents"][0]["verification_status"], "preliminary_match")


if __name__ == "__main__":
    unittest.main()
