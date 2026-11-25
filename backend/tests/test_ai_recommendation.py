import unittest

from app.services.ai_recommendation import get_recommendation_provider


class AIRecommendationTests(unittest.TestCase):
    def setUp(self):
        self.provider = get_recommendation_provider()
        self.profile = {
            "full_name": "Asha Rao",
            "date_of_birth": "1995-05-10",
            "gender": "female",
            "state": "Bihar",
            "district": "Patna",
            "occupation": "student",
            "category": "general",
            "annual_income": 800000,
            "land_holding_acres": None,
            "is_bpl": False,
            "is_disabled": False,
        }

    def test_confidence_improvement_documents_and_action_are_deterministic(self):
        results = [{
            "scheme_id": "scheme-1",
            "scheme_name": "Example Scheme",
            "match_percentage": 80,
            "matched_rules": ["category eq general"],
            "failed_rules": ["occupation eq farmer"],
        }]
        schemes = {
            "scheme-1": {
                "application_url": "https://scheme.example/apply",
                "benefits_summary": "Support up to ₹2 lakh",
            }
        }

        first = self.provider.build_eligibility_recommendations(
            self.profile, results, schemes, [], []
        )
        second = self.provider.build_eligibility_recommendations(
            self.profile, results, schemes, [], []
        )
        recommendation = first["results"][0]["ai_recommendation"]

        self.assertEqual(first, second)
        self.assertEqual(recommendation["confidence_score"], 77.3)
        self.assertIn("student", recommendation["improve_eligibility"][0].lower())
        self.assertIn("farmer", recommendation["improve_eligibility"][0].lower())
        self.assertEqual(recommendation["next_action"]["kind"], "upload_documents")
        self.assertTrue(all(doc["generic"] for doc in recommendation["recommended_documents"]))
        self.assertEqual(first["eligible_schemes"], ["Example Scheme"])

    def test_missing_field_is_identified_and_confidence_uses_match_rule_counts(self):
        result = self.provider.build_eligibility_recommendations(
            self.profile,
            [{
                "scheme_id": "scheme-2",
                "scheme_name": "Land Scheme",
                "match_percentage": 35,
                "matched_rules": ["occupation eq student"],
                "failed_rules": ["land_holding_acres gt 0 (Missing in profile)"],
            }],
            {"scheme-2": {}},
            [],
            [],
        )["results"][0]["ai_recommendation"]

        self.assertEqual(result["status"], "Not Eligible")
        self.assertEqual(result["confidence_score"], 54.8)
        self.assertIn("land holding information is missing", result["improve_eligibility"][0].lower())
        self.assertIsNone(result["next_action"])

    def test_dashboard_insights_are_based_on_supplied_user_data(self):
        insights = self.provider.build_dashboard_insights(
            self.profile,
            [{
                "scheme_id": "scheme-1",
                "scheme_name": "Example Scheme",
                "match_percentage": 80,
                "matched_rules": ["category eq general"],
                "failed_rules": [],
            }],
            {"scheme-1": {"application_url": "https://scheme.example/apply"}},
            [],
            [],
        )

        titles = [insight["title"] for insight in insights]
        self.assertIn("You qualify for 1 scheme.", titles)
        self.assertTrue(any("Example Scheme" in title for title in titles))
        self.assertTrue(any("income certificate" in item["description"].lower() for item in insights))
        self.assertTrue(any("0 of 4" in item["title"] for item in insights))

    def test_next_action_changes_with_profile_documents_and_checklist_state(self):
        base_result = {
            "scheme_id": "scheme-3",
            "scheme_name": "Example Scheme",
            "match_percentage": 75,
            "matched_rules": ["category eq general", "annual_income lte 600000", "state eq Bihar"],
            "failed_rules": ["land_holding_acres gt 0 (Missing in profile)"],
        }
        scheme = {"scheme-3": {"application_url": "https://scheme.example/apply"}}

        profile_action = self.provider.build_eligibility_recommendations(
            self.profile, [base_result], scheme, [], []
        )["results"][0]["ai_recommendation"]["next_action"]
        self.assertEqual(profile_action["kind"], "complete_profile")

        complete_documents = [
            {"document_category": category}
            for category in ("aadhaar", "income_certificate", "bank_passbook", "passport_photo")
        ]
        checklist = [{
            "scheme_id": "scheme-3",
            "status": "active",
            "checklist_items": [{"is_completed": False}],
        }]
        application_ready_result = {
            **base_result,
            "failed_rules": [],
        }
        checklist_action = self.provider.build_eligibility_recommendations(
            self.profile, [application_ready_result], scheme, checklist, complete_documents
        )["results"][0]["ai_recommendation"]["next_action"]
        self.assertEqual(checklist_action["kind"], "view_checklist")

        completed_checklist = [{
            **checklist[0],
            "status": "completed",
            "checklist_items": [{"is_completed": True}],
        }]
        apply_action = self.provider.build_eligibility_recommendations(
            self.profile, [application_ready_result], scheme, completed_checklist, complete_documents
        )["results"][0]["ai_recommendation"]["next_action"]
        self.assertEqual(apply_action["kind"], "apply_now")


if __name__ == "__main__":
    unittest.main()
