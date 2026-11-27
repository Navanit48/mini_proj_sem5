import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.ai.deterministic_provider import DeterministicAssistantProvider
from app.services.ai.groq_provider import GroqAssistantProvider


class DeterministicAssistantProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = DeterministicAssistantProvider()
        self.context = {
            "profile": {
                "full_name": "Asha Rao",
                "state": "Bihar",
                "occupation": "student",
                "annual_income": 200000,
            },
            "schemes": [
                {
                    "id": "scheme-1",
                    "name": "PMAY",
                    "description": "Housing support scheme.",
                    "ministry": "Ministry of Housing",
                    "benefits_summary": "Interest subsidy as recorded in scheme data.",
                    "eligibility_summary": "Applicants must meet scheme rules.",
                    "application_url": "https://example.gov/apply",
                }
            ],
            "eligibility_results": [
                {
                    "scheme_id": "scheme-1",
                    "scheme": {
                        "id": "scheme-1",
                        "name": "PMAY",
                        "benefits_summary": "Interest subsidy as recorded in scheme data.",
                        "application_url": "https://example.gov/apply",
                    },
                    "match_percentage": 82,
                    "status": "Eligible",
                    "matched_rules": ["annual income within limit"],
                    "failed_rules": [],
                },
                {
                    "scheme_id": "scheme-2",
                    "scheme": {"id": "scheme-2", "name": "PM Kisan"},
                    "match_percentage": 35,
                    "status": "Not Eligible",
                    "failed_rules": ["Occupation must be farmer"],
                },
            ],
            "recent_checked_schemes": [],
            "documents": [{"file_name": "aadhaar.pdf", "document_category": "aadhaar"}],
            "checklists": [{
                "scheme_name": "PMAY",
                "total_count": 2,
                "completed_count": 1,
                "pending_count": 1,
                "pending_titles": ["Upload income certificate"],
            }],
            "dashboard_stats": {
                "profile_completion": 57,
                "eligible_schemes": 1,
                "uploaded_documents": 1,
                "checklist_total": 2,
                "checklist_completed": 1,
            },
        }

    def test_eligibility_answer_uses_latest_saved_results_and_cards(self):
        result = self.provider.generate_response("What schemes am I eligible for?", self.context)
        self.assertIn("PMAY", result["content"])
        self.assertNotIn("PM Kisan", result["content"])
        self.assertEqual(result["scheme_cards"][0]["match_percentage"], 82)

    def test_failed_scheme_answer_uses_saved_failed_rule(self):
        result = self.provider.generate_response("Why am I not eligible for PM Kisan?", self.context)
        self.assertIn("Occupation must be farmer", result["content"])
        self.assertIn("35% match", result["content"])

    def test_scheme_explanation_only_uses_available_scheme_fields(self):
        result = self.provider.generate_response("Explain PMAY", self.context)
        self.assertIn("Ministry of Housing", result["content"])
        self.assertIn("Interest subsidy", result["content"])
        self.assertEqual(result["actions"][0]["href"], "https://example.gov/apply")

    def test_dashboard_and_pending_checklist_use_context_values(self):
        stats = self.provider.generate_response("Show my dashboard statistics", self.context)
        self.assertIn("57%", stats["content"])
        self.assertIn("1/2", stats["content"])
        checklist = self.provider.generate_response("Show my pending checklist", self.context)
        self.assertIn("Upload income certificate", checklist["content"])

    def test_unknown_scheme_is_not_fabricated(self):
        result = self.provider.generate_response("Explain Scheme Not In Database", self.context)
        self.assertIn("couldn't find a matching scheme", result["content"])
        self.assertEqual(result["scheme_cards"], [])

    def test_acronym_and_partial_scheme_names_match(self):
        context = {
            **self.context,
            "schemes": [
                {
                    "id": "pmay-id",
                    "name": "Pradhan Mantri Awas Yojana (PMAY)",
                    "description": "Housing for all.",
                    "ministry": "Ministry of Housing and Urban Affairs",
                },
                {
                    "id": "pmjay-id",
                    "name": "Ayushman Bharat - PMJAY",
                    "description": "Health insurance scheme.",
                    "ministry": "Ministry of Health and Family Welfare",
                },
                {
                    "id": "pmkisan-id",
                    "name": "PM Kisan Samman Nidhi",
                    "description": "Farmer income support.",
                    "ministry": "Ministry of Agriculture",
                },
            ],
        }
        pmay = self.provider.generate_response("Explain PMAY", context)
        self.assertIn("Pradhan Mantri Awas Yojana (PMAY)", pmay["content"])
        pmjay = self.provider.generate_response("Explain PMJAY", context)
        self.assertIn("Ayushman Bharat - PMJAY", pmjay["content"])
        pmkisan = self.provider.generate_response("Tell me about PM Kisan", context)
        self.assertIn("PM Kisan Samman Nidhi", pmkisan["content"])


class GroqAssistantProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = GroqAssistantProvider()
        self.context = {
            "profile": {"full_name": "Asha Rao", "state": "Bihar", "occupation": "farmer"},
            "schemes": [
                {
                    "id": "scheme-1",
                    "name": "PMAY",
                    "benefits_summary": "Housing subsidy",
                    "application_url": "https://example.gov/apply",
                }
            ],
            "eligibility_results": [
                {
                    "scheme_id": "scheme-1",
                    "scheme": {
                        "id": "scheme-1",
                        "name": "PMAY",
                        "benefits_summary": "Housing subsidy",
                        "application_url": "https://example.gov/apply",
                    },
                    "match_percentage": 85,
                    "status": "Eligible",
                    "matched_rules": ["income"],
                    "failed_rules": [],
                }
            ],
            "documents": [],
            "checklists": [],
            "dashboard_stats": {"profile_completion": 60, "eligible_schemes": 1},
            "history": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}],
        }

    def test_uses_groq_when_configured_and_validates_cards_and_actions(self):
        fake_groq = {
            "content": "You qualify for **PMAY** at **85%** based on your Bihar farmer profile.",
            "referenced_scheme_ids": ["scheme-1", "unknown-id"],
            "actions": [
                {"label": "Apply", "href": "https://example.gov/apply", "external": True},
                {"label": "Check docs", "href": "/documents", "external": False},
                {"label": "Phishing", "href": "https://evil.example", "external": True},
            ],
        }
        with (
            patch("app.services.ai.groq_provider.get_settings", return_value=SimpleNamespace(GROQ_API_KEY="gsk_real_key")),
            patch("app.services.ai.groq_provider.call_groq", return_value=fake_groq) as mock_call,
        ):
            result = self.provider.generate_response("Compare PMAY benefits for me", self.context)

        mock_call.assert_called_once()
        self.assertIn("85%", result["content"])
        self.assertEqual([c["id"] for c in result["scheme_cards"]], ["scheme-1"])
        self.assertEqual(
            result["actions"],
            [
                {"label": "Apply", "href": "https://example.gov/apply", "external": True},
                {"label": "Check docs", "href": "/documents", "external": False},
            ],
        )

    def test_falls_back_to_deterministic_when_groq_errors(self):
        with (
            patch("app.services.ai.groq_provider.get_settings", return_value=SimpleNamespace(GROQ_API_KEY="gsk_real_key")),
            patch("app.services.ai.groq_provider.call_groq", side_effect=RuntimeError("API error")),
        ):
            result = self.provider.generate_response("What schemes am I eligible for?", self.context)

        self.assertIn("PMAY", result["content"])
        self.assertEqual(result["scheme_cards"][0]["match_percentage"], 85)


if __name__ == "__main__":
    unittest.main()
