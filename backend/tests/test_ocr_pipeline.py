"""Pytest coverage for Groq extractor, RapidFuzz verifier, upload validation, and pipeline."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies import get_current_user
from app.main import app
from app.services.document_verifier import verify_extracted_document
from app.services.groq_extractor import extract_document_fields_with_groq
from app.services.ocr_service import process_document_ocr


def _make_groq_response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


class _FakeGroqClient:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls = 0
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **_kwargs):
        idx = min(self.calls, len(self._responses) - 1)
        self.calls += 1
        return _make_groq_response(self._responses[idx])


def test_groq_extractor_valid_json_and_masks_aadhaar(monkeypatch):
    fake_client = _FakeGroqClient([
        '{"name": "Asha Rao", "dob": "1995-05-01", "gender": "Female", "masked_id": "1234 5678 9012"}'
    ])
    monkeypatch.setattr("app.services.groq_extractor.get_extractor_groq_client", lambda: fake_client)
    monkeypatch.setattr(
        "app.services.groq_extractor.get_settings",
        lambda: SimpleNamespace(GROQ_API_KEY="test-key", GROQ_MODEL="llama-3.3-70b-versatile"),
    )

    result = extract_document_fields_with_groq("Name: Asha Rao\n1234 5678 9012", "aadhaar")
    assert fake_client.calls == 1
    assert result["name"] == "Asha Rao"
    assert result["dob"] == "1995-05-01"
    assert result["gender"] == "Female"
    assert result["masked_id"] == "XXXX-XXXX-9012"
    assert "1234" not in result["masked_id"]
    assert "5678" not in result["masked_id"]


def test_groq_extractor_retries_once_on_invalid_json(monkeypatch):
    fake_client = _FakeGroqClient([
        "not valid json {{{",
        '{"name": "Ravi Verma", "annual_income": "120,000", "issuing_authority": "Tehsildar", "issue_date": "2026-01-10", "valid_till": "2027-01-10"}',
    ])
    monkeypatch.setattr("app.services.groq_extractor.get_extractor_groq_client", lambda: fake_client)
    monkeypatch.setattr(
        "app.services.groq_extractor.get_settings",
        lambda: SimpleNamespace(GROQ_API_KEY="test-key", GROQ_MODEL="llama-3.3-70b-versatile"),
    )

    result = extract_document_fields_with_groq("Sample income certificate text", "income_certificate")
    assert fake_client.calls == 2
    assert result["name"] == "Ravi Verma"
    assert result["annual_income"] == 120000.0
    assert result["valid_till"] == "2027-01-10"


def test_groq_extractor_missing_fields_stay_null_and_fallback_works(monkeypatch):
    fake_client = _FakeGroqClient(["invalid json", "still invalid json"])
    monkeypatch.setattr("app.services.groq_extractor.get_extractor_groq_client", lambda: fake_client)
    monkeypatch.setattr(
        "app.services.groq_extractor.get_settings",
        lambda: SimpleNamespace(GROQ_API_KEY="test-key", GROQ_MODEL="llama-3.3-70b-versatile"),
    )

    sample_text = "Caste Certificate\nApplicant Name: Meena Devi\nCategory: Scheduled Caste"
    result = extract_document_fields_with_groq(sample_text, "caste_certificate")
    assert fake_client.calls == 2
    assert result["name"] == "Meena Devi"
    assert result["category"] == "sc"
    assert result["issued_date"] is None


def test_document_verifier_exact_match():
    profile = {
        "full_name": "Asha Rao",
        "date_of_birth": "1995-05-01",
        "annual_income": 120000,
        "category": "obc",
    }
    extracted = {
        "name": "asha rao",
        "dob": "01/05/1995",
        "annual_income": 120000,
        "category": "OBC",
        "valid_till": "2027-03-31",
    }
    result = verify_extracted_document(
        "income_certificate",
        extracted,
        profile,
        ocr_confidence=0.92,
        min_confidence=0.80,
        reference_date=date(2026, 6, 1),
    )
    assert result["verification_status"] == "verified"
    assert result["mismatch_details"] == []
    assert result["field_results"]["name"]["status"] == "match"
    assert result["field_results"]["dob"]["status"] == "match"


def test_document_verifier_name_mismatch():
    profile = {"full_name": "Asha Rao"}
    extracted = {"name": "Suresh Kumar"}
    result = verify_extracted_document(
        "aadhaar",
        extracted,
        profile,
        ocr_confidence=0.94,
        min_confidence=0.80,
    )
    assert result["verification_status"] == "mismatch"
    assert len(result["mismatch_details"]) == 1
    assert result["mismatch_details"][0]["field"] == "name"
    assert "does not match" in result["mismatch_details"][0]["reason"]


def test_document_verifier_expired_certificate():
    profile = {"full_name": "Asha Rao", "annual_income": 90000}
    extracted = {
        "name": "Asha Rao",
        "annual_income": 90000,
        "valid_till": "2024-12-31",
    }
    result = verify_extracted_document(
        "income_certificate",
        extracted,
        profile,
        ocr_confidence=0.95,
        min_confidence=0.80,
        reference_date=date(2026, 1, 15),
    )
    assert result["verification_status"] == "mismatch"
    assert any(item["field"] == "valid_till" for item in result["mismatch_details"])
    assert result["field_results"]["valid_till"]["status"] == "expired"


def test_document_verifier_low_confidence_sets_needs_review():
    profile = {"full_name": "Asha Rao", "date_of_birth": "1995-05-01"}
    extracted = {"name": "Asha Rao", "dob": "1995-05-01"}
    result = verify_extracted_document(
        "aadhaar",
        extracted,
        profile,
        ocr_confidence=0.62,
        min_confidence=0.80,
    )
    assert result["verification_status"] == "needs_review"
    assert result["mismatch_details"] == []


def test_upload_validation_rejects_bad_type_and_oversize():
    user_id = str(uuid4())
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)
    try:
        client = TestClient(app)

        bad_type = client.post(
            "/api/v1/documents/upload",
            data={"doc_type": "aadhaar"},
            files={"file": ("notes.txt", b"hello world", "text/plain")},
        )
        assert bad_type.status_code == 400
        assert "not allowed" in bad_type.json()["detail"].lower()

        oversize_payload = b"%PDF-1.4" + (b"0" * (5 * 1024 * 1024 + 100))
        oversize = client.post(
            "/api/v1/documents/upload",
            data={"doc_type": "aadhaar"},
            files={"file": ("big.pdf", oversize_payload, "application/pdf")},
        )
        assert oversize.status_code == 400
        assert "5mb" in oversize.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


class _FakeTableQuery:
    def __init__(self, store, name):
        self.store = store
        self.name = name
        self.op = "select"
        self.filters = []
        self.payload = None
        self.single = False

    def select(self, *_args, **_kwargs):
        self.op = "select"
        return self

    def update(self, payload):
        self.op = "update"
        self.payload = payload
        return self

    def upsert(self, payload, **_kwargs):
        self.op = "upsert"
        self.payload = payload
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def maybe_single(self):
        self.single = True
        return self

    def execute(self):
        rows = self.store.setdefault(self.name, [])
        if self.op == "upsert":
            existing = next((r for r in rows if r.get("document_id") == self.payload.get("document_id")), None)
            if existing:
                existing.update(self.payload)
                return SimpleNamespace(data=[existing])
            row = {"id": str(uuid4()), **self.payload}
            rows.append(row)
            return SimpleNamespace(data=[row])
        filtered = [r for r in rows if all(r.get(k) == v for k, v in self.filters)]
        if self.op == "update":
            for r in filtered:
                r.update(self.payload)
            return SimpleNamespace(data=filtered)
        data = (filtered[0] if filtered else None) if self.single else list(filtered)
        return SimpleNamespace(data=data)


class _FakeSupabase:
    def __init__(self, data):
        self.data = data

    def table(self, name):
        return _FakeTableQuery(self.data, name)


def test_verified_document_completes_matching_checklist_item():
    user_id = str(uuid4())
    doc_id = str(uuid4())
    checklist_id = str(uuid4())
    db = _FakeSupabase({
        "documents": [{
            "id": doc_id,
            "user_id": user_id,
            "file_name": "aadhaar.jpg",
            "file_type": "image/jpeg",
            "storage_path": f"{user_id}/aadhaar.jpg",
            "doc_type": "aadhaar",
            "status": "pending",
        }],
        "ocr_results": [],
        "user_profiles": [{
            "user_id": user_id,
            "full_name": "Asha Rao",
            "date_of_birth": "1995-05-01",
        }],
        "checklists": [{"id": checklist_id, "user_id": user_id, "status": "active"}],
        "checklist_items": [{
            "id": str(uuid4()),
            "checklist_id": checklist_id,
            "title": "Upload Aadhaar card",
            "description": "Provide Aadhaar identity verification",
            "is_completed": False,
        }],
        "application_documents": [],
    })

    with (
        patch("app.services.ocr_service.get_supabase_client", return_value=db),
        patch("app.services.ocr_service.download_file", return_value=b"\xff\xd8\xff\xe0dummy"),
        patch(
            "app.services.ocr_service.extract_text_from_document",
            return_value=("Name: Asha Rao\nDOB: 01/05/1995\n1234 5678 9012", 0.93),
        ),
        patch(
            "app.services.ocr_service.extract_document_fields_with_groq",
            return_value={"name": "Asha Rao", "dob": "1995-05-01", "gender": "Female", "masked_id": "XXXX-XXXX-9012"},
        ),
    ):
        process_document_ocr(doc_id, user_id, f"{user_id}/aadhaar.jpg", "image/jpeg", "aadhaar")

    doc = db.data["documents"][0]
    assert doc["status"] == "completed"
    assert doc["verification_status"] == "verified"
    assert "1234 5678" not in (doc["raw_text"] or "")
    assert "XXXX-XXXX-9012" in (doc["raw_text"] or "")
    assert db.data["checklist_items"][0]["is_completed"] is True
    assert db.data["checklists"][0]["status"] == "completed"
