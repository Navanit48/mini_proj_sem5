import io
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import httpx

from app.dependencies import get_current_user
from app.main import app
from app.services.eligibility_engine import evaluate_eligibility
from app.services.ocr_service import _extract_text_from_file


class _NoneMaybeSingleQuery:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.op = "select"
        self.payload = None
        self.is_maybe_single = False

    def select(self, *_args, **_kwargs):
        self.op = "select"
        return self

    def upsert(self, payload, **_kwargs):
        self.op = "upsert"
        self.payload = payload
        return self

    def eq(self, *_args):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args):
        return self

    def maybe_single(self):
        self.is_maybe_single = True
        return self

    def execute(self):
        if self.op == "upsert":
            row = {
                "id": "profile-1",
                **self.payload,
            }
            self.client.profiles[self.payload["user_id"]] = row
            return SimpleNamespace(data=[row])
        if self.is_maybe_single:
            return None
        return SimpleNamespace(data=[], count=0)


class _NoneMaybeSingleSupabase:
    def __init__(self):
        self.profiles = {}

    def table(self, name):
        return _NoneMaybeSingleQuery(self, name)


class CoreFixesTests(unittest.IsolatedAsyncioTestCase):
    async def test_maybe_single_none_responses_do_not_crash_routes(self):
        user_id = str(uuid4())
        supabase = _NoneMaybeSingleSupabase()
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=user_id,
            email="asha@example.com",
            user_metadata={"full_name": "Asha Rao"},
        )
        try:
            with (
                patch("app.routers.auth.get_supabase_client", return_value=supabase),
                patch("app.routers.schemes.get_supabase_client", return_value=supabase),
                patch("app.routers.eligibility.get_supabase_client", return_value=supabase),
                patch("app.routers.checklist.get_supabase_client", return_value=supabase),
                patch("app.routers.documents.get_supabase_client", return_value=supabase),
                patch("app.routers.analytics.get_supabase_client", return_value=supabase),
                patch("app.routers.applications.get_supabase_client", return_value=supabase),
            ):
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    me = await client.get("/api/v1/auth/me")
                    self.assertEqual(me.status_code, 200, me.text)
                    self.assertEqual(me.json()["profile"]["full_name"], "Asha Rao")

                    updated = await client.put(
                        "/api/v1/auth/profile",
                        json={"gender": "female", "annual_income": 0},
                    )
                    self.assertEqual(updated.status_code, 200, updated.text)
                    self.assertEqual(updated.json()["annual_income"], 0)

                    scheme_404 = await client.get("/api/v1/schemes/missing-id")
                    self.assertEqual(scheme_404.status_code, 404)

                    check_404 = await client.get("/api/v1/eligibility/history/missing-id")
                    self.assertEqual(check_404.status_code, 404)

                    checklist_404 = await client.get("/api/v1/checklists/missing-id")
                    self.assertEqual(checklist_404.status_code, 404)

                    app_404 = await client.get("/api/v1/applications/missing-id")
                    self.assertEqual(app_404.status_code, 404)

                    dashboard = await client.get("/api/v1/analytics/dashboard")
                    self.assertEqual(dashboard.status_code, 200, dashboard.text)
        finally:
            app.dependency_overrides.clear()

    def test_empty_string_in_profile_is_treated_as_missing(self):
        results = evaluate_eligibility(
            {"occupation": "   "},
            [
                {
                    "scheme_id": "scheme-1",
                    "schemes": {"name": "MGNREGA", "is_active": True},
                    "rule_definition": {
                        "operator": "and",
                        "conditions": [{"field": "occupation", "op": "eq", "value": "farmer"}],
                    },
                }
            ],
        )
        self.assertEqual(results[0]["match_percentage"], 0.0)
        self.assertIn("(Missing in profile)", results[0]["failed_rules"][0])

    def test_pdf_ocr_converts_pages_to_images(self):
        class _FakePage:
            def save(self, fh, format="JPEG"):
                fh.write(b"\xff\xd8\xff\xe0fake-jpeg")

        class _FakeEngine:
            def __init__(self):
                self.calls = 0

            def ocr(self, _path, cls=True):
                self.calls += 1
                return [[[[[0, 0]], (f"Page {self.calls} text", 0.9)]]]

        fake_engine = _FakeEngine()
        fake_pdf2image = SimpleNamespace(convert_from_bytes=lambda _bytes, dpi=200: [_FakePage(), _FakePage()])
        with (
            patch("app.services.ocr_service.get_ocr_engine", return_value=fake_engine),
            patch.dict(sys.modules, {"pdf2image": fake_pdf2image}),
        ):
            text, confidence = _extract_text_from_file(b"%PDF-1.4", "application/pdf")

        self.assertEqual(fake_engine.calls, 2)
        self.assertIn("Page 1 text", text)
        self.assertIn("Page 2 text", text)
        self.assertAlmostEqual(confidence, 0.9)

    async def test_auth_returns_503_when_supabase_unreachable(self):
        class _FailingAuth:
            def sign_up(self, _payload):
                raise httpx.ConnectError("[Errno 8] nodename nor servname provided, or not known")

            def sign_in_with_password(self, _payload):
                raise httpx.ConnectError("[Errno 8] nodename nor servname provided, or not known")

        fake_client = SimpleNamespace(auth=_FailingAuth())
        with (
            patch("app.routers.auth.get_supabase_anon_client", return_value=fake_client),
            patch("app.routers.auth.get_supabase_client", return_value=fake_client),
        ):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                reg = await client.post(
                    "/api/v1/auth/register",
                    json={"email": "a@example.com", "password": "Password123!", "full_name": "Asha"},
                )
                self.assertEqual(reg.status_code, 503, reg.text)
                self.assertIn("Cannot reach Supabase Auth service", reg.json()["detail"])

                login = await client.post(
                    "/api/v1/auth/login",
                    json={"email": "a@example.com", "password": "Password123!"},
                )
                self.assertEqual(login.status_code, 503, login.text)
                self.assertIn("Cannot reach Supabase Auth service", login.json()["detail"])


if __name__ == "__main__":
    unittest.main()
