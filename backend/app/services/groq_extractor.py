"""Structured field extraction from OCR text using Groq JSON mode with regex fallback."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from groq import Groq
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from app.config import get_settings
from app.services.document_verification import (
    _extract_applicant_name,
    _extract_income,
    _extract_labeled_value,
    _normalize,
)

logger = logging.getLogger(__name__)


def mask_aadhaar_number(value: Any) -> Optional[str]:
    """Ensure only the last 4 digits of an Aadhaar number are ever stored."""
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    if len(digits) < 4:
        return None
    return f"XXXX-XXXX-{digits[-4:]}"


def _clean_optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    if not text or text.lower() in {"null", "none", "n/a", "na", "unknown"}:
        return None
    return text[:200]


class AadhaarFields(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    masked_id: Optional[str] = None

    @field_validator("name", "dob", "gender", mode="before")
    @classmethod
    def _clean_str(cls, v: Any) -> Optional[str]:
        return _clean_optional_str(v)

    @field_validator("masked_id", mode="before")
    @classmethod
    def _mask_id(cls, v: Any) -> Optional[str]:
        return mask_aadhaar_number(v)


class IncomeCertificateFields(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    annual_income: Optional[float] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[str] = None
    valid_till: Optional[str] = None

    @field_validator("name", "issuing_authority", "issue_date", "valid_till", mode="before")
    @classmethod
    def _clean_str(cls, v: Any) -> Optional[str]:
        return _clean_optional_str(v)

    @field_validator("annual_income", mode="before")
    @classmethod
    def _parse_income(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        if isinstance(v, (int, float)):
            return float(v)
        cleaned = re.sub(r"[^\d.]", "", str(v))
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None


class CasteCertificateFields(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    category: Optional[str] = None
    issued_date: Optional[str] = None

    @field_validator("name", "category", "issued_date", mode="before")
    @classmethod
    def _clean_str(cls, v: Any) -> Optional[str]:
        return _clean_optional_str(v)


class BankPassbookFields(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    account_holder: Optional[str] = None
    ifsc: Optional[str] = None

    @field_validator("name", "account_holder", mode="before")
    @classmethod
    def _clean_str(cls, v: Any) -> Optional[str]:
        return _clean_optional_str(v)

    @field_validator("ifsc", mode="before")
    @classmethod
    def _clean_ifsc(cls, v: Any) -> Optional[str]:
        cleaned = _clean_optional_str(v)
        return cleaned.upper() if cleaned else None


class PhotoFields(BaseModel):
    model_config = ConfigDict(extra="ignore")


SCHEMA_BY_DOC_TYPE: dict[str, type[BaseModel]] = {
    "aadhaar": AadhaarFields,
    "income_certificate": IncomeCertificateFields,
    "caste_certificate": CasteCertificateFields,
    "bank_passbook": BankPassbookFields,
    "photo": PhotoFields,
}

EXPECTED_KEYS_BY_DOC_TYPE: dict[str, tuple[str, ...]] = {
    "aadhaar": ("name", "dob", "gender", "masked_id"),
    "income_certificate": ("name", "annual_income", "issuing_authority", "issue_date", "valid_till"),
    "caste_certificate": ("name", "category", "issued_date"),
    "bank_passbook": ("name", "account_holder", "ifsc"),
    "photo": (),
}


def get_extractor_groq_client() -> Groq:
    """Create a Groq SDK client using configured API credentials."""
    settings = get_settings()
    return Groq(api_key=settings.GROQ_API_KEY)


def regex_extract_fields(raw_text: str, doc_type: str) -> dict[str, Any]:
    """Deterministic regex fallback extractor when Groq is unavailable or invalid."""
    schema_cls = SCHEMA_BY_DOC_TYPE.get(doc_type, PhotoFields)
    if doc_type == "photo" or not raw_text.strip():
        return schema_cls().model_dump()

    name = _extract_applicant_name(raw_text)
    payload: dict[str, Any] = {}

    if doc_type == "aadhaar":
        dob = _extract_labeled_value(raw_text, r"\bdate of birth\b|\bdob\b|\byear of birth\b")
        if not dob:
            dob_match = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2})\b", raw_text)
            dob = dob_match.group(1) if dob_match else None
        gender = _extract_labeled_value(raw_text, r"\bgender\b|\bsex\b")
        if not gender:
            gender_match = re.search(r"\b(male|female|transgender|other)\b", raw_text, re.IGNORECASE)
            gender = gender_match.group(1).title() if gender_match else None
        aadhaar_match = re.search(r"(?:\d{4}|[Xx]{4})[\s-]?(?:\d{4}|[Xx]{4})[\s-]?(\d{4})\b", raw_text)
        payload = {
            "name": name,
            "dob": dob,
            "gender": gender,
            "masked_id": mask_aadhaar_number(aadhaar_match.group(0)) if aadhaar_match else None,
        }
    elif doc_type == "income_certificate":
        payload = {
            "name": name,
            "annual_income": _extract_income(raw_text),
            "issuing_authority": _extract_labeled_value(
                raw_text, r"issuing\s+authority|issued\s+by|authority|tahsildar|tehsildar"
            ),
            "issue_date": _extract_labeled_value(raw_text, r"issue\s+date|issued\s+date|date\s+of\s+issue"),
            "valid_till": _extract_labeled_value(raw_text, r"valid\s+till|valid\s+upto|valid\s+until|expiry\s+date"),
        }
    elif doc_type == "caste_certificate":
        cat_match = re.search(r"\b(scheduled\s+caste|scheduled\s+tribe|obc|ews|sc|st)\b", raw_text, re.IGNORECASE)
        category = None
        if cat_match:
            normalized_cat = _normalize(cat_match.group(1))
            category = {
                "scheduled caste": "sc",
                "scheduled tribe": "st",
                "obc": "obc",
                "ews": "ews",
                "sc": "sc",
                "st": "st",
            }.get(normalized_cat, normalized_cat)
        payload = {
            "name": name,
            "category": category,
            "issued_date": _extract_labeled_value(raw_text, r"issued?\s+date|date\s+of\s+issue"),
        }
    elif doc_type == "bank_passbook":
        holder = _extract_labeled_value(raw_text, r"account\s+holder(?:\s+name)?|customer\s+name") or name
        ifsc_match = re.search(r"\b([A-Z]{4}0[A-Z0-9]{6})\b", raw_text.upper())
        payload = {
            "name": name or holder,
            "account_holder": holder,
            "ifsc": ifsc_match.group(1) if ifsc_match else None,
        }

    return schema_cls(**payload).model_dump()


def extract_document_fields_with_groq(raw_text: str, doc_type: str) -> dict[str, Any]:
    """
    Extract structured fields for `doc_type` via Groq JSON mode, validated by Pydantic.
    Retries once on invalid JSON and falls back to regex extraction if Groq fails.
    """
    schema_cls = SCHEMA_BY_DOC_TYPE.get(doc_type, PhotoFields)
    if doc_type == "photo" or not raw_text or not raw_text.strip():
        return schema_cls().model_dump()

    settings = get_settings()
    if not settings.GROQ_API_KEY.strip():
        return regex_extract_fields(raw_text, doc_type)

    expected_keys = EXPECTED_KEYS_BY_DOC_TYPE[doc_type]
    system_prompt = (
        "You extract structured data from Indian government document OCR text.\n"
        f"Document type: {doc_type}\n"
        f"Return STRICT JSON containing ONLY these keys: {list(expected_keys)}.\n"
        "Rules:\n"
        "- Use null for any missing or unclear field. Never guess or fabricate values.\n"
        "- For aadhaar masked_id, return ONLY the last 4 digits formatted as XXXX-XXXX-1234.\n"
        "- For annual_income, return a plain number (or null).\n"
        "- For dates, prefer YYYY-MM-DD when unambiguous, otherwise the exact date string from the text."
    )
    user_prompt = f"Extract fields from this {doc_type} OCR text:\n\n{raw_text}"

    client = get_extractor_groq_client()
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=512,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("Groq response JSON is not an object")
            validated = schema_cls(**parsed)
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            logger.warning(
                "Groq extraction invalid output on attempt %d for doc_type=%s (%s)",
                attempt + 1,
                doc_type,
                type(exc).__name__,
            )
            if attempt == 0:
                continue
        except Exception as exc:
            logger.warning(
                "Groq extraction call failed for doc_type=%s (%s)",
                doc_type,
                type(exc).__name__,
            )
            break

    return regex_extract_fields(raw_text, doc_type)
