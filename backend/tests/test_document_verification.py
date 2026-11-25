import unittest

from app.services.document_verification import verify_document


class DocumentVerificationTests(unittest.TestCase):
    def test_income_certificate_extracts_and_matches_profile_without_external_ai(self):
        result = verify_document(
            "Income Certificate\nName: Asha Rao\nAnnual Income: Rs. 1,80,000",
            "general",
            {"full_name": "Asha Rao", "annual_income": 180000},
            0.95,
        )

        self.assertEqual(result["detected_document_type"], "income_certificate")
        self.assertEqual(result["extracted_fields"]["annual_income"], 180000)
        self.assertEqual(result["verification_status"], "preliminary_match")
        self.assertGreaterEqual(result["confidence_score"], 90)
        self.assertIn("preliminary", result["validation_summary"].lower())

    def test_mismatch_is_reported_and_marked_for_manual_review(self):
        result = verify_document(
            "Income Certificate\nName: Asha Rao\nAnnual Income: ₹1,80,000",
            "income_certificate",
            {"full_name": "Asha Rao", "annual_income": 150000},
            0.96,
        )

        self.assertEqual(result["verification_status"], "needs_review")
        self.assertEqual(result["mismatches"][0]["field"], "annual_income")
        self.assertEqual(result["mismatches"][0]["profile_value"], 150000)

    def test_unreadable_text_does_not_claim_a_match(self):
        result = verify_document("", "aadhaar", {"full_name": "Asha Rao"}, 0)

        self.assertEqual(result["verification_status"], "needs_review")
        self.assertEqual(result["confidence_score"], 0)
        self.assertTrue(result["warnings"])

    def test_ignores_father_name_and_certificate_number(self):
        result = verify_document(
            "Income Certificate No: 987654\nFather's Name: Mohan Rao\nApplicant Name: Asha Rao\nAnnual Income: Rs. 1,80,000",
            "income_certificate",
            {"full_name": "Asha Rao", "annual_income": 180000},
            0.95,
        )

        self.assertEqual(result["extracted_fields"]["full_name"], "Asha Rao")
        self.assertEqual(result["extracted_fields"]["annual_income"], 180000)
        self.assertEqual(result["verification_status"], "preliminary_match")


if __name__ == "__main__":
    unittest.main()
