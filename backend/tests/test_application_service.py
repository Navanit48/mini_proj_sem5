import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.services.application_service import (
    get_application,
    progress_application_workflow,
    submit_application,
)


class FakeQuery:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.operation = "select"
        self.filters = []
        self.membership = []
        self.payload = None
        self.single = False
        self.ordering = None
        self.limit_count = None

    def select(self, *_args, **_kwargs):
        self.operation = "select"
        return self

    def insert(self, payload):
        self.operation, self.payload = "insert", payload
        return self

    def update(self, payload):
        self.operation, self.payload = "update", payload
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def in_(self, key, values):
        self.membership.append((key, values))
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
        rows = self.client.rows.setdefault(self.table, [])
        if self.operation == "insert":
            values = self.payload if isinstance(self.payload, list) else [self.payload]
            inserted = []
            for value in values:
                row = dict(value)
                row.setdefault("id", str(uuid4()))
                row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
                row.setdefault("submitted_at", datetime.now(timezone.utc).isoformat())
                row.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
                row.setdefault("occurred_at", datetime.now(timezone.utc).isoformat())
                rows.append(row)
                inserted.append(row)
            return SimpleNamespace(data=inserted)

        filtered = [
            row for row in rows
            if all(row.get(key) == value for key, value in self.filters)
            and all(row.get(key) in values for key, values in self.membership)
        ]
        if self.operation == "update":
            for row in filtered:
                row.update(self.payload)
            return SimpleNamespace(data=filtered)
        if self.operation == "delete":
            self.client.rows[self.table] = [row for row in rows if row not in filtered]
            return SimpleNamespace(data=filtered)
        if self.ordering:
            key, desc = self.ordering
            filtered.sort(key=lambda row: row.get(key) or "", reverse=desc)
        if self.limit_count is not None:
            filtered = filtered[:self.limit_count]
        return SimpleNamespace(data=(filtered[0] if filtered else None) if self.single else filtered)


class FakeSupabase:
    def __init__(self, user_id):
        self.rows = {
            "user_profiles": [{
                "user_id": user_id, "full_name": "Asha Rao", "date_of_birth": "1995-05-10",
                "gender": "female", "state": "Bihar", "district": "Patna",
                "occupation": "student", "category": "general", "annual_income": 180000,
                "land_holding_acres": None, "is_bpl": False, "is_disabled": False,
            }],
            "schemes": [{"id": "scheme-1", "is_active": True, "name": "Housing Support", "ministry": "Housing", "category": "Housing"}],
            "eligibility_checks": [{"id": "check-1", "user_id": user_id, "checked_at": "2026-11-25T10:00:00+00:00", "submitted_profile": {}}],
            "eligibility_results": [{"check_id": "check-1", "scheme_id": "scheme-1", "match_percentage": 82, "matched_rules": ["annual income within limit"], "failed_rules": []}],
            "documents": [{"id": "doc-1", "user_id": user_id, "file_name": "income.pdf", "file_type": "application/pdf", "document_category": "income_certificate", "status": "completed", "file_size_bytes": 100, "uploaded_at": "2026-11-25T10:00:00+00:00"}],
            "ocr_results": [{"document_id": "doc-1", "verification_status": "preliminary_match", "confidence_score": 94, "extracted_fields": {"annual_income": 180000}, "validation_summary": "Fields match."}],
        }

    def table(self, name):
        return FakeQuery(self, name)


class ApplicationServiceTests(unittest.TestCase):
    def test_submission_snapshots_profile_documents_and_internal_timeline(self):
        user_id = str(uuid4())
        supabase = FakeSupabase(user_id)
        application = submit_application(
            supabase,
            user_id,
            "scheme-1",
            {"district": "Gaya", "annual_income": 180000},
            ["doc-1"],
            "check-1",
        )

        progress_application_workflow(supabase, application["id"], user_id)
        tracked = get_application(supabase, user_id, application["id"])

        self.assertRegex(tracked["application_code"], r"^AF\d{4}[A-F0-9]{6}$")
        self.assertEqual(tracked["profile_snapshot"]["district"], "Gaya")
        self.assertEqual(tracked["documents"][0]["verification_status"], "preliminary_match")
        self.assertEqual(tracked["status"], "ready_for_government_submission")
        self.assertEqual(len(tracked["timeline"]), 4)
        self.assertEqual(tracked["progress"], 75)
        self.assertTrue(all(stage["occurred_at"] is None for stage in tracked["external_stages"]))

    def test_other_users_documents_are_rejected(self):
        user_id = str(uuid4())
        supabase = FakeSupabase(user_id)
        with self.assertRaises(Exception) as raised:
            submit_application(supabase, user_id, "scheme-1", {}, ["someone-elses-doc"], None)
        self.assertEqual(getattr(raised.exception, "status_code", None), 400)


if __name__ == "__main__":
    unittest.main()
