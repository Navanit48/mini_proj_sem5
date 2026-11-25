"""Local, rule based checks for AidFlow's preliminary document review."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from datetime import datetime
from typing import Any


DOCUMENT_TYPES: dict[str, dict[str, Any]] = {
    "aadhaar": {
        "label": "Aadhaar Card",
        "keywords": ("aadhaar", "आधार", "unique identification authority"),
        "required_fields": ("full_name",),
    },
    "pan": {
        "label": "PAN Card",
        "keywords": ("permanent account number", "income tax department", "pan"),
        "required_fields": ("full_name",),
    },
    "income_certificate": {
        "label": "Income Certificate",
        "keywords": ("income certificate", "annual income", "family income", "आय प्रमाण"),
        "required_fields": ("full_name", "annual_income"),
    },
    "caste_certificate": {
        "label": "Caste Certificate",
        "keywords": ("caste certificate", "scheduled caste", "scheduled tribe", "जाति प्रमाण"),
        "required_fields": ("full_name", "category"),
    },
    "domicile": {
        "label": "Domicile Certificate",
        "keywords": ("domicile", "residence certificate", "मूल निवास"),
        "required_fields": ("full_name", "state"),
    },
    "bank_passbook": {
        "label": "Bank Passbook",
        "keywords": ("passbook", "account number", "ifsc", "ifsc code"),
        "required_fields": ("full_name",),
    },
    "ration_card": {
        "label": "Ration Card",
        "keywords": ("ration card", "public distribution system", "खाद्य सुरक्षा"),
        "required_fields": ("full_name",),
    },
    "land_record": {
        "label": "Land Record",
        "keywords": ("land record", "land holding", "survey number", "khasra"),
        "required_fields": ("full_name", "land_holding_acres"),
    },
    "marksheet": {
        "label": "Marksheet / Certificate",
        "keywords": ("marksheet", "mark sheet", "board of", "certificate of education"),
        "required_fields": ("full_name",),
    },
    "passport_photo": {
        "label": "Passport-size Photo",
        "keywords": (),
        "required_fields": (),
    },
    "general": {"label": "Unclassified document", "keywords": (), "required_fields": ()},
}

FIELD_LABELS = {
    "full_name": "name",
    "annual_income": "annual income",
    "date_of_birth": "date of birth",
    "gender": "gender",
    "category": "social category",
    "state": "state",
    "district": "district",
    "land_holding_acres": "land holding",
}


def _normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _extract_labeled_value(text: str, labels: str) -> str | None:
    match = re.search(
        rf"(?:{labels})\s*[:\-]?\s*([^\n\r]+)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    value = re.split(r"\s{2,}|\s+(?:date of birth|dob|gender|address)\s*:", match.group(1), maxsplit=1, flags=re.I)[0]
    value = re.sub(r"\s+", " ", value).strip(" :-")
    return value[:160] or None


def _normalized_date(value: Any) -> str:
    raw = str(value or "").strip()
    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(raw, date_format).date().isoformat()
        except ValueError:
            continue
    return _normalize(raw)


def _keyword_present(text: str, keyword: str) -> bool:
    if len(keyword) <= 3 and keyword.isascii() and keyword.isalnum():
        return re.search(rf"\b{re.escape(keyword)}\b", text) is not None
    return keyword in text


def _extract_applicant_name(text: str) -> str | None:
    """Extract applicant name without capturing father/mother/husband/scheme names."""
    skip_prefix = re.compile(
        r"\b(?:father|mother|husband|wife|spouse|guardian|son|daughter|scheme|bank|branch)\b",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        if skip_prefix.search(line):
            continue
        value = _extract_labeled_value(line, r"(?:applicant(?:'s)?\s+name|beneficiary\s+name|\bname\b|नाम)")
        if value:
            return value
    return None


def _extract_income(text: str) -> float | None:
    for pattern in (
        r"(?:annual\s+income|family\s+income|total\s+income|gross\s+income|income\s+per\s+annum)"
        r"[^\d₹\n\r]{0,30}(?:₹|rs\.?\s*)?\s*([\d,]+(?:\.\d+)?)",
        r"\bincome\b(?!\s+(?:certificate|tax))[^\d₹\n\r]{0,20}(?:₹|rs\.?\s*)?\s*([\d,]+(?:\.\d+)?)",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def extract_document_fields(text: str, document_type: str) -> dict[str, Any]:
    """Extract only explicit labelled values; never infer absent field values."""
    extracted: dict[str, Any] = {}
    name = _extract_applicant_name(text)
    if name:
        extracted["full_name"] = name

    if document_type == "income_certificate":
        income = _extract_income(text)
        if income is not None:
            extracted["annual_income"] = income

    if document_type == "aadhaar":
        dob = _extract_labeled_value(text, r"\bdate of birth\b|\bdob\b|\byear of birth\b")
        if dob:
            extracted["date_of_birth"] = dob
        gender = _extract_labeled_value(text, r"\bgender\b|\bsex\b")
        if gender:
            extracted["gender"] = gender

    if document_type == "caste_certificate":
        category = re.search(r"\b(scheduled\s+caste|scheduled\s+tribe|obc|ews|sc|st)\b", text, re.I)
        if category:
            raw_category = _normalize(category.group(1))
            extracted["category"] = {
                "scheduled caste": "sc", "scheduled tribe": "st",
                "obc": "obc", "ews": "ews", "sc": "sc", "st": "st",
            }.get(raw_category, raw_category)

    if document_type == "domicile":
        state = _extract_labeled_value(text, r"state|राज्य")
        district = _extract_labeled_value(text, r"district|जिला")
        if state:
            extracted["state"] = state
        if district:
            extracted["district"] = district

    if document_type == "land_record":
        land = re.search(r"([\d,.]+)\s*(?:acre|acres|hectare|hectares)", text, re.I)
        if land:
            try:
                acres = float(land.group(1).replace(",", ""))
                extracted["land_holding_acres"] = acres * 2.47105 if "hectare" in land.group(0).casefold() else acres
            except ValueError:
                pass
    return extracted


def verify_document(
    text: str,
    declared_type: str,
    profile: dict[str, Any],
    ocr_confidence: float,
) -> dict[str, Any]:
    normalized_text = text.casefold()
    type_scores = {
        category: sum(_keyword_present(normalized_text, keyword.casefold()) for keyword in definition["keywords"])
        for category, definition in DOCUMENT_TYPES.items()
        if category not in {"general", "passport_photo"}
    }
    detected_type = max(type_scores, key=type_scores.get) if type_scores and max(type_scores.values()) else "general"
    matched_keywords = type_scores.get(detected_type, 0)
    type_confidence = min(1.0, 0.55 + 0.15 * matched_keywords) if detected_type != "general" else 0.0
    warnings: list[str] = []
    if detected_type == "general" and declared_type in DOCUMENT_TYPES:
        detected_type = declared_type
        type_confidence = 0.35
        warnings.append("Document type could not be identified confidently from its text; the selected upload type is shown.")
    elif detected_type != declared_type and declared_type != "general":
        warnings.append(f"Selected type is {DOCUMENT_TYPES.get(declared_type, DOCUMENT_TYPES['general'])['label']}, but the text resembles {DOCUMENT_TYPES[detected_type]['label']}.")

    extracted = extract_document_fields(text, detected_type)
    required_fields = DOCUMENT_TYPES[detected_type]["required_fields"]
    missing_fields = [field for field in required_fields if extracted.get(field) is None]
    if not text.strip():
        warnings.append("No readable text was extracted. Check image quality and upload a clear scan.")
    if missing_fields:
        warnings.append("Required information was not found: " + ", ".join(FIELD_LABELS[field] for field in missing_fields) + ".")

    mismatches: list[dict[str, Any]] = []
    compared = 0
    matched = 0
    for field, document_value in extracted.items():
        profile_value = profile.get(field)
        if profile_value is None or str(profile_value).strip() == "":
            warnings.append(f"Your profile has no {FIELD_LABELS.get(field, field)} value to compare.")
            continue
        compared += 1
        if field == "full_name":
            similarity = SequenceMatcher(None, _normalize(document_value), _normalize(profile_value)).ratio()
            is_match = similarity >= 0.88
        elif field == "annual_income":
            try:
                is_match = abs(float(document_value) - float(profile_value)) <= max(1.0, abs(float(profile_value)) * 0.01)
            except (TypeError, ValueError):
                is_match = False
        elif field == "land_holding_acres":
            try:
                is_match = abs(float(document_value) - float(profile_value)) <= 0.05
            except (TypeError, ValueError):
                is_match = False
        elif field == "date_of_birth":
            is_match = _normalized_date(document_value) == _normalized_date(profile_value)
        else:
            is_match = _normalize(document_value) == _normalize(profile_value)
        if is_match:
            matched += 1
        else:
            mismatches.append({
                "field": field,
                "label": FIELD_LABELS.get(field, field.replace("_", " ")),
                "document_value": document_value,
                "profile_value": profile_value,
                "message": f"The {FIELD_LABELS.get(field, field.replace('_', ' '))} on this document does not match your saved profile.",
            })

    completion = (len(required_fields) - len(missing_fields)) / len(required_fields) if required_fields else 1.0
    consistency = matched / compared if compared else (0.5 if not required_fields else 0.0)
    confidence = 0 if not text.strip() else round(
        100 * (
            0.45 * max(0.0, min(1.0, ocr_confidence))
            + 0.25 * type_confidence
            + 0.20 * completion
            + 0.10 * consistency
        )
    )
    if mismatches:
        verification_status = "needs_review"
        summary = f"{len(mismatches)} profile mismatch(es) found. Review the extracted values before using this document."
    elif not text.strip() or missing_fields or type_confidence < 0.5 or ocr_confidence < 0.45:
        verification_status = "needs_review"
        summary = "Some required details could not be confirmed. Review this document manually."
    else:
        verification_status = "preliminary_match"
        summary = "Extracted details match the available profile fields in this preliminary check."

    return {
        "detected_document_type": detected_type,
        "document_type_confidence": round(type_confidence * 100),
        "extracted_fields": extracted,
        "confidence_score": confidence,
        "verification_status": verification_status,
        "validation_summary": summary,
        "mismatches": mismatches,
        "warnings": list(dict.fromkeys(warnings)),
    }
