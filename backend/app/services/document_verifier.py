"""Rule-based document verification comparing Groq/OCR extracted fields against user profile."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from rapidfuzz import fuzz

from app.config import get_settings

NAME_MATCH_THRESHOLD = 85

CATEGORY_ALIASES = {
    "sc": "sc",
    "scheduled caste": "sc",
    "st": "st",
    "scheduled tribe": "st",
    "obc": "obc",
    "other backward class": "obc",
    "ews": "ews",
    "economically weaker section": "ews",
    "general": "general",
    "gen": "general",
    "ur": "general",
    "unreserved": "general",
}


def _normalize_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y/%m/%d",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d %b %Y",
        "%d %B %Y",
    ):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_category(value: Any) -> str:
    cleaned = _normalize_text(value)
    return CATEGORY_ALIASES.get(cleaned, cleaned)


def verify_extracted_document(
    doc_type: str,
    extracted_fields: dict[str, Any] | None,
    profile: dict[str, Any] | None,
    ocr_confidence: float,
    min_confidence: float | None = None,
    reference_date: date | None = None,
) -> dict[str, Any]:
    """
    Compare extracted_fields against user profile using deterministic rules only.
    Returns verification_status ('verified' | 'mismatch' | 'needs_review'),
    per-field results with reasons, and mismatch_details.
    """
    settings = get_settings()
    threshold = settings.OCR_MIN_CONFIDENCE if min_confidence is None else min_confidence
    conf_ratio = (
        float(ocr_confidence) / 100.0 if float(ocr_confidence or 0.0) > 1.0 else float(ocr_confidence or 0.0)
    )
    conf_ratio = max(0.0, min(1.0, conf_ratio))
    today = reference_date or date.today()

    fields = dict(extracted_fields or {})
    prof = dict(profile or {})

    field_results: dict[str, dict[str, Any]] = {}
    mismatch_details: list[dict[str, Any]] = []
    warnings: list[str] = []

    # 1. Fuzzy Name Match (rapidfuzz, case-insensitive, threshold 85)
    doc_name = fields.get("name") or fields.get("account_holder") or fields.get("full_name")
    prof_name = prof.get("full_name")
    if doc_name is not None:
        if prof_name and str(prof_name).strip():
            norm_doc = _normalize_text(doc_name)
            norm_prof = _normalize_text(prof_name)
            score = round(fuzz.token_sort_ratio(norm_doc, norm_prof), 2)
            matched = score >= NAME_MATCH_THRESHOLD
            reason = (
                f"Name matches profile ({score}% similarity)."
                if matched
                else f"Name '{doc_name}' does not match profile name '{prof_name}' ({score}% < {NAME_MATCH_THRESHOLD}%)."
            )
            field_results["name"] = {
                "status": "match" if matched else "mismatch",
                "document_value": doc_name,
                "profile_value": prof_name,
                "score": score,
                "reason": reason,
            }
            if not matched:
                mismatch_details.append({
                    "field": "name",
                    "label": "name",
                    "document_value": doc_name,
                    "profile_value": prof_name,
                    "score": score,
                    "message": reason,
                    "reason": reason,
                })
        else:
            reason = "Profile has no full_name set to verify against."
            field_results["name"] = {
                "status": "missing_profile",
                "document_value": doc_name,
                "profile_value": None,
                "reason": reason,
            }
            warnings.append(reason)

    # 2. Date of Birth equality
    doc_dob_raw = fields.get("dob") or fields.get("date_of_birth")
    prof_dob_raw = prof.get("date_of_birth")
    if doc_dob_raw is not None:
        if prof_dob_raw and str(prof_dob_raw).strip():
            doc_dob = _parse_date(doc_dob_raw)
            prof_dob = _parse_date(prof_dob_raw)
            if doc_dob and prof_dob:
                matched = doc_dob == prof_dob
                reason = (
                    "Date of birth matches profile."
                    if matched
                    else f"DOB '{doc_dob.isoformat()}' does not match profile DOB '{prof_dob.isoformat()}'."
                )
            else:
                matched = _normalize_text(doc_dob_raw) == _normalize_text(prof_dob_raw)
                reason = (
                    "Date of birth matches profile."
                    if matched
                    else f"DOB '{doc_dob_raw}' does not match profile DOB '{prof_dob_raw}'."
                )
            field_results["dob"] = {
                "status": "match" if matched else "mismatch",
                "document_value": str(doc_dob_raw),
                "profile_value": str(prof_dob_raw),
                "reason": reason,
            }
            if not matched:
                mismatch_details.append({
                    "field": "dob",
                    "label": "date of birth",
                    "document_value": str(doc_dob_raw),
                    "profile_value": str(prof_dob_raw),
                    "message": reason,
                    "reason": reason,
                })
        else:
            reason = "Profile has no date of birth set to verify against."
            field_results["dob"] = {
                "status": "missing_profile",
                "document_value": str(doc_dob_raw),
                "profile_value": None,
                "reason": reason,
            }
            warnings.append(reason)

    # 3. Annual Income comparison
    doc_income = fields.get("annual_income")
    prof_income = prof.get("annual_income")
    if doc_income is not None:
        if prof_income is not None and str(prof_income).strip() != "":
            try:
                doc_val = float(doc_income)
                prof_val = float(prof_income)
                matched = abs(doc_val - prof_val) <= max(1.0, abs(prof_val) * 0.01)
                reason = (
                    "Annual income matches profile."
                    if matched
                    else f"Document annual income ({doc_val:,.0f}) does not match profile income ({prof_val:,.0f})."
                )
            except (TypeError, ValueError):
                matched = False
                reason = f"Could not compare document income '{doc_income}' with profile income '{prof_income}'."
            field_results["annual_income"] = {
                "status": "match" if matched else "mismatch",
                "document_value": doc_income,
                "profile_value": prof_income,
                "reason": reason,
            }
            if not matched:
                mismatch_details.append({
                    "field": "annual_income",
                    "label": "annual income",
                    "document_value": doc_income,
                    "profile_value": prof_income,
                    "message": reason,
                    "reason": reason,
                })
        else:
            reason = "Profile has no annual income set to verify against."
            field_results["annual_income"] = {
                "status": "missing_profile",
                "document_value": doc_income,
                "profile_value": None,
                "reason": reason,
            }
            warnings.append(reason)

    # 4. Social Category match
    doc_cat = fields.get("category")
    prof_cat = prof.get("category")
    if doc_cat is not None:
        if prof_cat and str(prof_cat).strip():
            matched = _normalize_category(doc_cat) == _normalize_category(prof_cat)
            reason = (
                "Category matches profile."
                if matched
                else f"Certificate category '{doc_cat}' does not match profile category '{prof_cat}'."
            )
            field_results["category"] = {
                "status": "match" if matched else "mismatch",
                "document_value": doc_cat,
                "profile_value": prof_cat,
                "reason": reason,
            }
            if not matched:
                mismatch_details.append({
                    "field": "category",
                    "label": "category",
                    "document_value": doc_cat,
                    "profile_value": prof_cat,
                    "message": reason,
                    "reason": reason,
                })
        else:
            reason = "Profile has no social category set to verify against."
            field_results["category"] = {
                "status": "missing_profile",
                "document_value": doc_cat,
                "profile_value": None,
                "reason": reason,
            }
            warnings.append(reason)

    # 5. Expiry check using valid_till
    valid_till_raw = fields.get("valid_till")
    if valid_till_raw is not None:
        expiry_date = _parse_date(valid_till_raw)
        if expiry_date is None:
            reason = f"Could not parse certificate validity date '{valid_till_raw}'."
            field_results["valid_till"] = {
                "status": "unparsed",
                "document_value": str(valid_till_raw),
                "reason": reason,
            }
            warnings.append(reason)
        elif expiry_date < today:
            reason = f"Document expired on {expiry_date.isoformat()}."
            field_results["valid_till"] = {
                "status": "expired",
                "document_value": expiry_date.isoformat(),
                "reason": reason,
            }
            mismatch_details.append({
                "field": "valid_till",
                "label": "validity",
                "document_value": expiry_date.isoformat(),
                "profile_value": f">= {today.isoformat()}",
                "message": reason,
                "reason": reason,
            })
        else:
            field_results["valid_till"] = {
                "status": "valid",
                "document_value": expiry_date.isoformat(),
                "reason": f"Document is valid until {expiry_date.isoformat()}.",
            }

    # 6. Confidence & completeness check -> decide status purely by rules
    has_extracted_data = any(v is not None and v != "" for v in fields.values())
    low_confidence = conf_ratio < threshold
    if low_confidence:
        warnings.append(
            f"OCR confidence ({round(conf_ratio * 100, 1)}%) is below minimum threshold ({round(threshold * 100, 1)}%)."
        )
    if doc_type != "photo" and not has_extracted_data:
        warnings.append("No structured fields could be extracted from the document.")

    if mismatch_details:
        verification_status = "mismatch"
        summary = f"{len(mismatch_details)} issue(s) found during verification. Review mismatch details and re-upload if needed."
    elif low_confidence or (doc_type != "photo" and not has_extracted_data):
        verification_status = "needs_review"
        summary = "Low OCR confidence or incomplete extracted fields. Manual review is required."
    else:
        verification_status = "verified"
        summary = "Extracted document details match your profile."

    return {
        "verification_status": verification_status,
        "field_results": field_results,
        "mismatch_details": mismatch_details,
        "warnings": list(dict.fromkeys(warnings)),
        "validation_summary": summary,
        "ocr_confidence": round(conf_ratio, 4),
        "confidence_score": round(conf_ratio * 100, 2),
        "detected_document_type": doc_type,
        "document_type_confidence": 100.0 if has_extracted_data else 0.0,
    }
