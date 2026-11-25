"""Deterministic recommendation provider for eligibility and dashboard insights.

The provider contract keeps API response construction independent from any future
model provider. This implementation only transforms profile, rule, scheme,
document, and checklist data; it never calls an external AI service.
"""

from __future__ import annotations

import ast
import math
import re
from datetime import date
from typing import Any, Protocol

from app.services.eligibility_engine import ELIGIBLE_MATCH_THRESHOLD

PROFILE_FIELDS = (
    "full_name",
    "date_of_birth",
    "gender",
    "state",
    "district",
    "occupation",
    "category",
    "annual_income",
    "land_holding_acres",
    "is_bpl",
    "is_disabled",
)

GENERIC_DOCUMENTS = (
    {"name": "Aadhaar card", "category": "aadhaar"},
    {"name": "Income certificate", "category": "income_certificate"},
    {"name": "Bank passbook", "category": "bank_passbook"},
    {"name": "Passport-size photo", "category": "passport_photo"},
)

RULE_PATTERN = re.compile(
    r"^(?P<field>[a-zA-Z_][a-zA-Z0-9_]*)\s+"
    r"(?P<op>eq|neq|gt|gte|lt|lte|in|contains)\s+"
    r"(?P<target>.*?)(?P<missing> \(Missing in profile\))?$"
)

FIELD_LABELS = {
    "annual_income": "annual income",
    "land_holding_acres": "land holding",
    "occupation": "occupation",
    "category": "social category",
    "state": "state",
    "district": "district",
    "gender": "gender",
    "date_of_birth": "date of birth",
    "is_bpl": "BPL status",
    "is_disabled": "disability status",
    "full_name": "full name",
}


class RecommendationProvider(Protocol):
    """Stable service interface for future deterministic or model-backed providers."""

    def build_eligibility_recommendations(
        self,
        profile: dict[str, Any],
        results: list[dict[str, Any]],
        schemes: dict[str, dict[str, Any]],
        checklists: list[dict[str, Any]],
        documents: list[dict[str, Any]],
    ) -> dict[str, Any]: ...

    def build_dashboard_insights(
        self,
        profile: dict[str, Any],
        results: list[dict[str, Any]],
        schemes: dict[str, dict[str, Any]],
        checklists: list[dict[str, Any]],
        documents: list[dict[str, Any]],
    ) -> list[dict[str, str]]: ...


def _present(value: Any) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


def _profile_strength(profile: dict[str, Any]) -> int:
    present = sum(_present(profile.get(field)) for field in PROFILE_FIELDS)
    return round(present / len(PROFILE_FIELDS) * 100)


def _parse_target(value: str) -> Any:
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        return value


def _format_rupees(value: Any) -> str:
    try:
        amount = str(abs(int(float(value))))
        if len(amount) > 3:
            last_three = amount[-3:]
            prefix = re.sub(r"(\d)(?=(\d{2})+(?!\d))", r"\1,", amount[:-3])
            amount = f"{prefix},{last_three}"
        sign = "-" if float(value) < 0 else ""
        return f"₹{sign}{amount}"
    except (TypeError, ValueError):
        return str(value)


def _format_value(field: str, value: Any) -> str:
    if field == "annual_income":
        return _format_rupees(value)
    if field == "land_holding_acres":
        return f"{value} acres"
    if field in {"occupation", "category", "gender"} and isinstance(value, str):
        return value.replace("-", " ").title()
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _explain_rule(description: str, profile: dict[str, Any], matched: bool) -> str:
    parsed = RULE_PATTERN.match(description)
    if not parsed:
        return description

    field = parsed.group("field")
    operator = parsed.group("op")
    target = _parse_target(parsed.group("target"))
    actual = profile.get(field)
    label = FIELD_LABELS.get(field, field.replace("_", " "))

    if not matched and parsed.group("missing"):
        return f"{label.capitalize()} information is missing from your profile."

    actual_text = _format_value(field, actual) if actual is not None else None
    target_text = _format_value(field, target)
    if operator == "eq":
        requirement = f"must be {target_text}"
    elif operator == "neq":
        requirement = f"must not be {target_text}"
    elif operator == "gt":
        requirement = f"must be greater than {target_text}"
    elif operator == "gte":
        requirement = f"must be at least {target_text}"
    elif operator == "lt":
        requirement = f"must be below {target_text}"
    elif operator == "lte":
        requirement = f"must be at or below {target_text}"
    elif operator == "in":
        values = target if isinstance(target, list) else [target]
        requirement = f"must be one of {', '.join(str(item) for item in values)}"
    elif operator == "contains":
        requirement = f"must include {target_text}"
    else:
        requirement = "must satisfy the scheme rule"

    if matched:
        if actual_text is None:
            return f"Your {label} satisfies the scheme rule ({requirement})."
        return f"Your {label} ({actual_text}) satisfies the rule: it {requirement}."

    if actual_text is None:
        return f"Your {label} must be added to your profile; it {requirement}."
    if operator in {"lt", "lte", "gt", "gte"}:
        comparison = "above" if operator in {"lt", "lte"} else "below"
        return (
            f"Your {label} ({actual_text}) is {comparison} the scheme requirement "
            f"({requirement}). Review this condition using your current information."
        )
    if operator == "eq":
        return (
            f"Your {label} is {actual_text}; this scheme requires {target_text}. "
            "Update your profile only if the current value is incorrect."
        )
    return f"Your {label} is {actual_text}; this scheme requires that it {requirement}."


def _scheme_profile_completeness(
    result: dict[str, Any], profile: dict[str, Any], fallback: int
) -> int:
    fields = set()
    for description in (result.get("matched_rules") or []) + (result.get("failed_rules") or []):
        parsed = RULE_PATTERN.match(description)
        if parsed:
            fields.add(parsed.group("field"))
    if not fields:
        return fallback
    return round(sum(_present(profile.get(field)) for field in fields) / len(fields) * 100)


def _deadline_score(deadline: Any) -> float:
    if not deadline:
        return 50.0
    try:
        days_left = (date.fromisoformat(str(deadline)[:10]) - date.today()).days
    except ValueError:
        return 50.0
    if days_left < 0:
        return 0.0
    if days_left <= 30:
        return 100.0
    if days_left <= 90:
        return 80.0
    return 60.0


def _benefit_score(summary: Any) -> float:
    if not summary:
        return 50.0
    match = re.search(
        r"₹\s*([\d,.]+)\s*(crore|crores|cr|lakh|lakhs|lac|lacs|thousand)?",
        str(summary),
        flags=re.IGNORECASE,
    )
    if not match:
        return 50.0
    try:
        amount = float(match.group(1).replace(",", ""))
    except ValueError:
        return 50.0
    unit = (match.group(2) or "").lower()
    multiplier = 10_000_000 if unit in {"crore", "crores", "cr"} else (
        100_000 if unit in {"lakh", "lakhs", "lac", "lacs"} else (
            1_000 if unit == "thousand" else 1
        )
    )
    return min(100.0, round(math.log10(max(amount * multiplier, 1)) * 12, 1))


def _checklist_for_scheme(checklists: list[dict[str, Any]], scheme_id: str) -> dict[str, Any] | None:
    return next((item for item in checklists if item.get("scheme_id") == scheme_id), None)


def _document_recommendations(
    scheme: dict[str, Any], documents: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    required = scheme.get("required_documents")
    if not isinstance(required, list) or not required:
        required = GENERIC_DOCUMENTS
    uploaded_categories = {item.get("document_category") for item in documents}
    generic = required is GENERIC_DOCUMENTS
    return [
        {
            "name": item["name"],
            "category": item["category"],
            "uploaded": item["category"] in uploaded_categories,
            "generic": generic,
        }
        for item in required
        if isinstance(item, dict) and item.get("name") and item.get("category")
    ]


class DeterministicRecommendationProvider:
    """Recommendation generator using only current application data and fixed rules."""

    def build_eligibility_recommendations(
        self,
        profile: dict[str, Any],
        results: list[dict[str, Any]],
        schemes: dict[str, dict[str, Any]],
        checklists: list[dict[str, Any]],
        documents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        profile_strength = _profile_strength(profile)
        recommendations = []

        for source in results:
            result = dict(source)
            scheme = schemes.get(str(result.get("scheme_id")), {})
            match = float(result.get("match_percentage") or 0)
            matched = result.get("matched_rules") or []
            failed = result.get("failed_rules") or []
            status = (
                "Eligible" if match >= ELIGIBLE_MATCH_THRESHOLD else
                "Partially Eligible" if match >= 40 else "Not Eligible"
            )
            reasons = [_explain_rule(rule, profile, True) for rule in matched]
            improvements = [_explain_rule(rule, profile, False) for rule in failed]
            if not reasons and not improvements:
                reasons = ["No rule details were returned for this scheme."]

            total_rules = len(matched) + len(failed)
            matched_rule_score = (len(matched) / total_rules * 100) if total_rules else 0
            confidence = round(
                0.5 * match + 0.3 * profile_strength + 0.2 * matched_rule_score,
                1,
            )
            checklist = _checklist_for_scheme(checklists, str(result.get("scheme_id")))
            checklist_items = (checklist or {}).get("checklist_items") or []
            checklist_total = len(checklist_items)
            checklist_completed = sum(item.get("is_completed") is True for item in checklist_items)
            scheme_profile = _scheme_profile_completeness(result, profile, profile_strength)
            score = round(
                0.45 * match
                + 0.25 * scheme_profile
                + 0.20 * _deadline_score(scheme.get("deadline"))
                + 0.10 * _benefit_score(scheme.get("benefits_summary")),
                1,
            )
            priority = (
                {"stars": 5, "label": "Highest Priority", "class": "highest"}
                if score >= 75 else
                {"stars": 4, "label": "Medium Priority", "class": "medium"}
                if score >= 55 else
                {"stars": 2, "label": "Low Priority", "class": "low"}
            )
            recommended_documents = (
                _document_recommendations(scheme, documents)
                if status == "Eligible" else []
            )
            missing_documents = [item for item in recommended_documents if not item["uploaded"]]

            if status != "Eligible":
                next_action = None
                recommendation = (
                    "Review the unmet conditions and update your profile if the information is missing or has changed."
                )
            elif any("missing from your profile" in item.lower() for item in improvements):
                next_action = {"label": "Complete Profile", "kind": "complete_profile", "href": "/eligibility"}
                recommendation = "Complete the missing profile information, then review your eligibility again."
            elif missing_documents:
                next_action = {"label": "Upload Documents", "kind": "upload_documents", "href": "/documents"}
                recommendation = "Prepare the recommended documents before starting your application."
            elif checklist and checklist_total > checklist_completed:
                next_action = {"label": "View Checklist", "kind": "view_checklist", "href": "/checklists"}
                recommendation = "Continue your saved application checklist before applying."
            elif scheme.get("application_url"):
                next_action = {
                    "label": "Apply Now",
                    "kind": "apply_now",
                    "href": scheme["application_url"],
                    "external": True,
                }
                recommendation = "Your rule results meet the eligibility threshold. Review the official scheme page before applying."
            else:
                next_action = {"label": "View Checklist", "kind": "view_checklist", "href": "/checklists"}
                recommendation = "Review the scheme details and prepare an application checklist."

            result["ai_recommendation"] = {
                "status": status,
                "reasons": reasons,
                "recommendation": recommendation,
                "improve_eligibility": improvements,
                "confidence_score": confidence,
                "priority_score": score if status == "Eligible" else None,
                "priority": priority if status == "Eligible" else None,
                "recommended_documents": recommended_documents,
                "next_action": next_action,
                "checklist_progress": {
                    "total": checklist_total,
                    "completed": checklist_completed,
                } if checklist else None,
            }
            result["_priority_score"] = score if status == "Eligible" else -1
            recommendations.append(result)

        recommendations.sort(
            key=lambda item: (
                item.get("_priority_score", -1),
                float(item.get("match_percentage") or 0),
            ),
            reverse=True,
        )
        for item in recommendations:
            item.pop("_priority_score", None)

        eligible = [
            item["scheme_name"] for item in recommendations
            if item["ai_recommendation"]["status"] == "Eligible"
        ]
        near_misses = [
            item["scheme_name"] for item in recommendations
            if 50 <= float(item.get("match_percentage") or 0) < ELIGIBLE_MATCH_THRESHOLD
        ]
        return {
            "profile_strength": profile_strength,
            "eligible_schemes": eligible,
            "near_misses": near_misses,
            "evaluated_count": len(recommendations),
            "results": recommendations,
        }

    def build_dashboard_insights(
        self,
        profile: dict[str, Any],
        results: list[dict[str, Any]],
        schemes: dict[str, dict[str, Any]],
        checklists: list[dict[str, Any]],
        documents: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        payload = self.build_eligibility_recommendations(
            profile, results, schemes, checklists, documents
        )
        insights: list[dict[str, str]] = []
        if results:
            count = len(payload["eligible_schemes"])
            insights.append({
                "id": "eligible-schemes",
                "type": "eligible",
                "title": f"You qualify for {count} scheme{'s' if count != 1 else ''}.",
                "description": f"{payload['evaluated_count']} schemes were evaluated using your saved eligibility results.",
                "action_label": "Review recommendations",
                "action_path": "/eligibility",
            })
            highest = next(
                (item for item in payload["results"] if item["ai_recommendation"]["priority"]),
                None,
            )
            if highest:
                action = highest["ai_recommendation"]["next_action"]
                insights.append({
                    "id": "highest-priority",
                    "type": "priority",
                    "title": f"Highest priority: {highest['scheme_name']}.",
                    "description": highest["ai_recommendation"]["recommendation"],
                    "action_label": action["label"],
                    "action_path": action["href"],
                })

            missing_by_scheme: dict[str, set[str]] = {}
            for item in payload["results"]:
                missing = set()
                for description in item.get("failed_rules") or []:
                    parsed = RULE_PATTERN.match(description)
                    if parsed and parsed.group("missing"):
                        missing.add(parsed.group("field"))
                if missing:
                    missing_by_scheme[item["scheme_id"]] = missing
            if missing_by_scheme:
                fields = sorted(set.union(*missing_by_scheme.values()))
                readable = FIELD_LABELS.get(fields[0], fields[0].replace("_", " "))
                insights.append({
                    "id": "profile-completion",
                    "type": "profile",
                    "title": f"Add your {readable} information.",
                    "description": (
                        f"At least one profile field is missing for {len(missing_by_scheme)} "
                        "evaluated schemes; complete it and run the check again."
                    ),
                    "action_label": "Complete Profile",
                    "action_path": "/eligibility",
                })

        uploaded = {item.get("document_category") for item in documents}
        uploaded_generic_count = sum(
            item["category"] in uploaded for item in GENERIC_DOCUMENTS
        )
        missing_generic_docs = [
            item for item in GENERIC_DOCUMENTS if item["category"] not in uploaded
        ]
        if documents or missing_generic_docs:
            missing_document = next(
                (doc for doc in missing_generic_docs if doc["category"] == "income_certificate"),
                missing_generic_docs[0] if missing_generic_docs else None,
            )
            document_description = (
                f"Add your {missing_document['name'].lower()} for general application preparation; "
                "document requirements vary by scheme."
                if missing_document else
                "All document types in the generic preparation list are present in your documents."
            )
            insights.append({
                "id": "document-preparation",
                "type": "documents",
                "title": (
                    f"You have uploaded {uploaded_generic_count} of {len(GENERIC_DOCUMENTS)} "
                    "generic recommended document types."
                ),
                "description": document_description,
                "action_label": "Upload Documents",
                "action_path": "/documents",
            })

        if checklists:
            active = next((item for item in checklists if item.get("status") != "completed"), None)
            if active:
                items = active.get("checklist_items") or []
                complete = sum(item.get("is_completed") is True for item in items)
                insights.append({
                    "id": "checklist-progress",
                    "type": "checklist",
                    "title": f"{complete} of {len(items)} checklist tasks are complete.",
                    "description": f"Continue the checklist for {active.get('scheme_name') or 'your selected scheme'}.",
                    "action_label": "View Checklist",
                    "action_path": "/checklists",
                })

        if not insights:
            missing_profile = next(
                (field for field in PROFILE_FIELDS if not _present(profile.get(field))),
                None,
            )
            if missing_profile:
                label = FIELD_LABELS.get(missing_profile, missing_profile.replace("_", " "))
                insights.append({
                    "id": "profile-completion",
                    "type": "profile",
                    "title": f"Add your {label} information.",
                    "description": (
                        "A more complete profile gives the eligibility checker more "
                        "information to evaluate."
                    ),
                    "action_label": "Complete Profile",
                    "action_path": "/eligibility",
                })
            else:
                insights.append({
                    "id": "run-eligibility",
                    "type": "suggestion",
                    "title": "Run an eligibility check to get scheme recommendations.",
                    "description": (
                        "Recommendations are generated from your saved profile and scheme rules."
                    ),
                    "action_label": "Check Eligibility",
                    "action_path": "/eligibility",
                })

        return insights[:5]


_provider: RecommendationProvider = DeterministicRecommendationProvider()


def get_recommendation_provider() -> RecommendationProvider:
    """Return the current provider; future integrations can replace this binding."""
    return _provider
