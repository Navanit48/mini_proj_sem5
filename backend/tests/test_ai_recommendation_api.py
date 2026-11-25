import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import httpx

from app.dependencies import get_current_user
from app.main import app


class FakeSupabaseQuery:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.operation = "select"
        self.filters = {}
        self.payload = None
        self.single = False
        self.count_exact = False
        self.columns = ""

    def select(self, columns, count=None):
        self.operation = "select"
        self.columns = columns
        self.client.selected_columns = columns
        self.count_exact = count == "exact"
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args):
        return self

    def maybe_single(self):
        self.single = True
        return self

    def execute(self):
        if self.operation == "insert":
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            inserted = []
            for payload in payloads:
                row = dict(payload)
                if self.table_name == "eligibility_checks":
                    row.update({
                        "id": str(uuid4()),
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                    })
                self.client.rows.setdefault(self.table_name, []).append(row)
                inserted.append(row)
            return SimpleNamespace(data=inserted, count=len(inserted))

        rows = self.client.rows.get(self.table_name, [])
        data = [
            dict(row) for row in rows
            if all(
                str(
                    row.get(key.split(".")[0], {}).get(key.split(".")[1])
                    if "." in key and isinstance(row.get(key.split(".")[0]), dict)
                    else row.get(key)
                ) == str(value)
                for key, value in self.filters.items()
            )
        ]
        if self.table_name == "eligibility_checks" and "eligibility_results" in self.columns:
            for check in data:
                check["eligibility_results"] = [
                    {
                        **result,
                        "schemes": self.client.scheme_by_id.get(result["scheme_id"], {}),
                    }
                    for result in self.client.rows.get("eligibility_results", [])
                    if result.get("check_id") == check["id"]
                ]
        if self.single:
            data = data[0] if data else None
        count = len(data) if isinstance(data, list) else int(data is not None)
        return SimpleNamespace(data=data, count=count if self.count_exact else None)


class FakeSupabase:
    def __init__(self, user_id):
        self.selected_columns = ""
        self.scheme_by_id = {
            "scheme-a": {
                "id": "scheme-a",
                "name": "Housing Support",
                "benefits_summary": "Support up to ₹2 lakh",
                "deadline": None,
                "application_url": "https://scheme.example/apply",
                "category": "housing",
            },
            "scheme-b": {
                "id": "scheme-b",
                "name": "Farmer Support",
                "benefits_summary": "Annual support",
                "deadline": None,
                "application_url": None,
                "category": "agriculture",
            },
        }
        self.rows = {
            "user_profiles": [{
                "user_id": user_id,
                "full_name": "Asha Rao",
                "date_of_birth": "1995-05-10",
                "gender": "female",
                "state": "Bihar",
                "district": "Patna",
                "occupation": "student",
                "category": "general",
                "annual_income": 200000,
                "land_holding_acres": None,
                "is_bpl": False,
                "is_disabled": False,
                "phone": "1234567890",
            }],
            "scheme_rules": [
                {
                    "scheme_id": "scheme-a",
                    "is_active": True,
                    "rule_definition": {
                        "operator": "and",
                        "conditions": [
                            {"field": "annual_income", "op": "lte", "value": 600000},
                            {"field": "category", "op": "eq", "value": "general"},
                        ],
                    },
                    "schemes": self.scheme_by_id["scheme-a"],
                },
                {
                    "scheme_id": "scheme-b",
                    "is_active": True,
                    "rule_definition": {
                        "operator": "and",
                        "conditions": [
                            {"field": "occupation", "op": "eq", "value": "farmer"},
                            {"field": "land_holding_acres", "op": "gt", "value": 0},
                        ],
                    },
                    "schemes": self.scheme_by_id["scheme-b"],
                },
            ],
            "eligibility_checks": [],
            "eligibility_results": [],
            "checklists": [{
                "user_id": user_id,
                "scheme_id": "scheme-a",
                "status": "active",
                "scheme_name": "Housing Support",
                "schemes": {"name": "Housing Support"},
                "checklist_items": [{"id": "task-1", "is_completed": False}],
            }],
            "checklist_items": [{
                "id": "task-1",
                "is_completed": False,
                "checklists": {"user_id": user_id},
            }],
            "documents": [{"user_id": user_id, "document_category": "aadhaar"}],
        }

    def table(self, name):
        return FakeSupabaseQuery(self, name)


class AIRecommendationAPITests(unittest.IsolatedAsyncioTestCase):
    async def test_eligibility_history_and_dashboard_routes_include_ai_data(self):
        user_id = str(uuid4())
        client_data = FakeSupabase(user_id)
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)

        original_table = client_data.table

        def tracked_table(name):
            query = original_table(name)
            return query

        client_data.table = tracked_table
        try:
            with (
                patch("app.routers.eligibility.get_supabase_client", return_value=client_data),
                patch("app.routers.analytics.get_supabase_client", return_value=client_data),
            ):
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.post("/api/v1/eligibility/check", json={})
                    self.assertEqual(response.status_code, 200, response.text)
                    payload = response.json()
                    self.assertEqual(payload["ai_summary"]["eligible_schemes"], ["Housing Support"])
                    self.assertEqual(len(payload["results"]), 2)
                    eligible = next(item for item in payload["results"] if item["scheme_id"] == "scheme-a")
                    self.assertEqual(eligible["ai_recommendation"]["status"], "Eligible")
                    self.assertIn("class", eligible["ai_recommendation"]["priority"])
                    self.assertEqual(eligible["ai_recommendation"]["next_action"]["kind"], "upload_documents")

                    history = await client.get("/api/v1/eligibility/history")
                    self.assertEqual(history.status_code, 200, history.text)
                    self.assertTrue(history.json()["checks"][0]["results"][0]["ai_recommendation"])

                    dashboard = await client.get("/api/v1/analytics/dashboard")
                    self.assertEqual(dashboard.status_code, 200, dashboard.text)
                    self.assertTrue(dashboard.json()["ai_insights"])
                    self.assertEqual(dashboard.json()["uploaded_documents"], 1)
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
