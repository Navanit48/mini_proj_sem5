import unittest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import patch

import httpx

from app.dependencies import get_current_user
from app.main import app
from test_application_service import FakeSupabase


class ApplicationAPITests(unittest.IsolatedAsyncioTestCase):
    async def test_preview_submit_list_and_detail_routes(self):
        user_id = str(uuid4())
        supabase = FakeSupabase(user_id)
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)
        try:
            with patch("app.routers.applications.get_supabase_client", return_value=supabase):
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    preview = await client.post(
                        "/api/v1/applications/preview",
                        json={"scheme_id": "scheme-1"},
                    )
                    self.assertEqual(preview.status_code, 200, preview.text)
                    self.assertEqual(preview.json()["eligibility"]["status"], "Eligible")
                    self.assertEqual(len(preview.json()["documents"]), 1)

                    submitted = await client.post(
                        "/api/v1/applications",
                        json={
                            "scheme_id": "scheme-1",
                            "profile_overrides": {"district": "Gaya"},
                            "document_ids": ["doc-1"],
                            "eligibility_check_id": "check-1",
                        },
                    )
                    self.assertEqual(submitted.status_code, 201, submitted.text)
                    payload = submitted.json()
                    self.assertRegex(payload["application_code"], r"^AF\d{4}[A-F0-9]{6}$")
                    self.assertEqual(payload["status"], "ready_for_government_submission")
                    self.assertEqual(payload["profile_snapshot"]["district"], "Gaya")
                    self.assertTrue(all(stage["occurred_at"] is None for stage in payload["external_stages"]))

                    listing = await client.get("/api/v1/applications")
                    self.assertEqual(listing.status_code, 200, listing.text)
                    self.assertEqual(listing.json()["total"], 1)

                    detail = await client.get(f"/api/v1/applications/{payload['id']}")
                    self.assertEqual(detail.status_code, 200, detail.text)
                    self.assertEqual(len(detail.json()["timeline"]), 4)
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
