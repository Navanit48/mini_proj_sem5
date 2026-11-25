"""Grounded assistant responses generated only from AidFlow database context."""

from __future__ import annotations

import re
from typing import Any


def _scheme_cards(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards = []
    for row in rows:
        scheme = row.get("scheme") or {}
        if not scheme.get("id") or not scheme.get("name"):
            continue
        cards.append({
            "id": str(scheme["id"]),
            "name": scheme["name"],
            "benefits_summary": scheme.get("benefits_summary"),
            "eligibility_summary": scheme.get("eligibility_summary"),
            "deadline": str(scheme["deadline"]) if scheme.get("deadline") else None,
            "application_url": scheme.get("application_url"),
            "match_percentage": row.get("match_percentage"),
            "status": row.get("status"),
        })
    return cards


class DeterministicAssistantProvider:
    """Answer supported questions with stored user, scheme, and activity data."""

    def generate_response(self, question: str, context: dict[str, Any]) -> dict[str, Any]:
        q = question.casefold()
        results = context.get("eligibility_results", [])
        eligible = [item for item in results if item.get("status") == "Eligible"]
        schemes = context.get("schemes", [])
        documents = context.get("documents", [])
        checklists = context.get("checklists", [])
        profile = context.get("profile", {})
        actions: list[dict[str, Any]] = []

        def answer(content: str, rows: list[dict[str, Any]] | None = None):
            return {"content": content, "scheme_cards": _scheme_cards(rows or []), "actions": actions}

        if any(term in q for term in ("dashboard", "statistics", "stats", "profile completion")):
            stats = context.get("dashboard_stats", {})
            content = (
                f"From your current saved data:\n\n"
                f"- Profile completion: **{stats.get('profile_completion', 0)}%**\n"
                f"- Eligible schemes in your latest check: **{stats.get('eligible_schemes', 0)}**\n"
                f"- Uploaded documents: **{stats.get('uploaded_documents', 0)}**\n"
                f"- Checklist items completed: **{stats.get('checklist_completed', 0)}/{stats.get('checklist_total', 0)}**"
            )
            actions.append({"label": "Open dashboard", "href": "/dashboard", "external": False})
            return answer(content)

        if "recent" in q or "last checked" in q:
            recent = context.get("recent_checked_schemes", [])
            unique = list({str(item.get("id")): item for item in reversed(recent) if item.get("id")}.values())
            if not unique:
                return answer("There are no saved eligibility checks yet.")
            return answer(
                "Schemes included in your recent eligibility checks:\n\n"
                + "\n".join(f"- {item.get('name', 'Scheme')}" for item in unique),
                [{"scheme": item} for item in unique],
            )

        if any(word in q for word in ("next", "what should i do", "what do i do")):
            steps = []
            missing = [
                label for field, label in (
                    ("full_name", "name"), ("state", "state"), ("district", "district"),
                    ("occupation", "occupation"), ("category", "category"),
                    ("annual_income", "annual income"), ("land_holding_acres", "land holding information"),
                ) if profile.get(field) is None or profile.get(field) == ""
            ]
            if missing:
                steps.append(f"Complete your profile: add {', '.join(missing)}.")
                actions.append({"label": "Complete profile", "href": "/eligibility", "external": False})
            if eligible:
                priority = eligible[0]
                name = priority.get("scheme", {}).get("name", "your highest-ranked eligible scheme")
                steps.append(f"Review and apply for **{name}** based on your latest eligibility check.")
                url = priority.get("scheme", {}).get("application_url")
                if url:
                    actions.append({"label": f"Apply for {name}", "href": url, "external": True})
            pending = [cl for cl in checklists if cl.get("pending_count", 0) > 0]
            if pending:
                steps.append(f"Complete {pending[0]['pending_count']} pending item(s) in your **{pending[0]['scheme_name']}** checklist.")
                actions.append({"label": "View checklists", "href": "/checklists", "external": False})
            if not steps:
                steps.append("Run an eligibility check to get scheme-specific next steps.")
                actions.append({"label": "Check eligibility", "href": "/eligibility", "external": False})
            return answer("Based on the information currently saved in AidFlow:\n\n" + "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1)), eligible[:1])

        if "checklist" in q or "pending task" in q:
            pending = [cl for cl in checklists if cl.get("pending_count", 0)]
            if not pending:
                content = "There are no pending checklist items in your saved checklists." if checklists else "You do not have a saved checklist yet. Open a scheme and create one to track its application steps."
                actions.append({"label": "View checklists", "href": "/checklists", "external": False})
                return answer(content)
            lines = [f"**{cl['scheme_name']}** ({cl['completed_count']}/{cl['total_count']} complete):" for cl in pending]
            lines.extend(f"- {item}" for cl in pending for item in cl.get("pending_titles", []))
            actions.append({"label": "Open checklists", "href": "/checklists", "external": False})
            return answer("Your pending checklist progress:\n\n" + "\n".join(lines))

        if any(term in q for term in ("document", "upload")):
            names = [doc.get("file_name") for doc in documents if doc.get("file_name")]
            categories = {str(doc.get("document_category", "")).casefold() for doc in documents}
            recommended = []
            for result in eligible:
                required = result.get("scheme", {}).get("required_documents") or []
                recommended.extend(item.get("name") for item in required if isinstance(item, dict) and item.get("name"))
            recommended = list(dict.fromkeys(recommended))
            lines = [f"You have uploaded {len(documents)} document(s)" + (f": {', '.join(names)}." if names else ".")]
            if recommended:
                lines.append("Documents listed for your eligible schemes: " + ", ".join(recommended) + ".")
            elif not eligible:
                lines.append("No latest eligible scheme result contains a document requirement list. Check a scheme's official instructions for its required documents.")
            else:
                lines.append("The scheme records do not include specific document requirements, so I can't confirm which documents are required.")
            if categories:
                lines.append("Recorded upload categories: " + ", ".join(sorted(categories)) + ".")
            actions.append({"label": "Open documents", "href": "/documents", "external": False})
            return answer("\n\n".join(lines), eligible)

        if "profile" in q or "missing" in q or "complete" in q:
            labels = {
                "full_name": "Full name", "date_of_birth": "Date of birth", "gender": "Gender",
                "state": "State", "district": "District", "occupation": "Occupation",
                "category": "Social category", "annual_income": "Annual income",
                "land_holding_acres": "Land holding", "is_bpl": "BPL status", "is_disabled": "Disability status",
            }
            missing = [label for key, label in labels.items() if profile.get(key) is None or profile.get(key) == ""]
            if missing:
                content = "These profile fields are currently empty and may be needed by scheme rules:\n\n" + "\n".join(f"- {item}" for item in missing)
                actions.append({"label": "Complete profile", "href": "/eligibility", "external": False})
            else:
                content = "All profile fields used by the assistant's completeness check have a saved value. Scheme-specific eligibility can still depend on the latest rule results."
            return answer(content)

        scheme_match = self._find_scheme(q, schemes)
        is_scheme_explanation = any(term in q for term in ("explain", "about", "what is", "tell me", "details"))
        if is_scheme_explanation and not scheme_match:
            return answer("I couldn't find a matching scheme in the active scheme records. Check the scheme name or browse the Schemes page.")
        if scheme_match and any(term in q for term in ("explain", "about", "what is", "tell me", "details")):
            fields = [
                ("description", "Description"), ("ministry", "Ministry"), ("benefits_summary", "Benefits"),
                ("eligibility_summary", "Eligibility"), ("deadline", "Deadline"),
            ]
            lines = [f"### {scheme_match.get('name')}"]
            for key, label in fields:
                if scheme_match.get(key):
                    lines.append(f"**{label}:** {scheme_match[key]}")
            if len(lines) == 1:
                lines.append("The scheme record does not currently include a description or eligibility details.")
            if scheme_match.get("application_url"):
                actions.append({"label": "Open official application page", "href": scheme_match["application_url"], "external": True})
            rows = [item for item in results if str(item.get("scheme", {}).get("id")) == str(scheme_match.get("id"))]
            return answer("\n\n".join(lines), rows)

        if any(term in q for term in ("why", "not eligible", "failed", "miss")):
            target = scheme_match or next((item.get("scheme") for item in results if item.get("status") != "Eligible"), None)
            result = next((item for item in results if item.get("scheme", {}).get("id") == (target or {}).get("id")), None)
            if not result:
                return answer("I don't have a saved eligibility result for that scheme yet. Run an eligibility check first.")
            failures = result.get("failed_rules", [])
            content = f"Your latest result for **{target.get('name')}** is **{result.get('status')}** ({result.get('match_percentage', 0)}% match)."
            content += "\n\nUnmatched rule details from that check:\n\n" + ("\n".join(f"- {item}" for item in failures) if failures else "- The saved result contains no failed-rule details.")
            return answer(content, [result])

        if any(term in q for term in ("benefit", "highest", "priority", "first", "eligible", "qualify", "scheme")):
            if not results:
                return answer("There are no saved eligibility results yet. Run an eligibility check to see which schemes match your profile.")
            rows = eligible if eligible else results
            if "benefit" in q:
                rows = [row for row in rows if row.get("scheme", {}).get("benefits_summary")]
                if not rows:
                    return answer("Your saved scheme records do not include benefit summaries, so I can't compare benefit values.")
                return answer("Benefit information available in your saved eligible scheme records:\n\n" + "\n".join(f"- **{row['scheme']['name']}:** {row['scheme']['benefits_summary']}" for row in rows), rows)
            heading = "Schemes matching your latest eligibility check:" if eligible else "Your latest eligibility results (none meet the eligible threshold):"
            lines = [f"- **{row['scheme'].get('name', 'Scheme')}** — {row.get('status')}, {row.get('match_percentage', 0)}% match" for row in rows]
            return answer(heading + "\n\n" + "\n".join(lines), rows)

        return answer("I can answer questions using your saved profile, scheme records, eligibility results, documents, and checklist activity. Try asking about your eligible schemes, a scheme's details, missing profile information, uploaded documents, or pending checklist tasks.")

    @staticmethod
    def _find_scheme(question: str, schemes: list[dict[str, Any]]) -> dict[str, Any] | None:
        normalized = " ".join(re.sub(r"[^a-z0-9 ]", " ", question.casefold()).split())
        exact_matches = []
        for scheme in schemes:
            name = scheme.get("name") or ""
            norm_name = " ".join(re.sub(r"[^a-z0-9 ]", " ", name.casefold()).split())
            if norm_name and norm_name in normalized:
                exact_matches.append(scheme)
        if exact_matches:
            return max(exact_matches, key=lambda item: len(item.get("name", "")))

        # Match parenthesized acronyms (e.g. "(PMAY)", "(NFSA)") or hyphenated abbreviations ("- PMJAY")
        question_tokens = set(normalized.split())
        for scheme in schemes:
            name = scheme.get("name") or ""
            for acronym in re.findall(r"\(([A-Za-z0-9]{3,})\)|-\s*([A-Za-z0-9]{3,})\b", name):
                token = (acronym[0] or acronym[1]).casefold()
                if token in question_tokens:
                    return scheme

        # Match distinctive scheme phrase after stripping question filler words
        stop_words = {
            "explain", "about", "what", "is", "tell", "me", "details", "detail",
            "why", "not", "eligible", "for", "am", "i", "failed", "miss",
            "the", "a", "an", "my", "on", "in", "of", "scheme", "yojana",
        }
        remaining = " ".join(token for token in normalized.split() if token not in stop_words)
        if len(remaining) >= 4:
            partial_matches = []
            for scheme in schemes:
                norm_name = " ".join(re.sub(r"[^a-z0-9 ]", " ", (scheme.get("name") or "").casefold()).split())
                if remaining in norm_name:
                    partial_matches.append(scheme)
            if len(partial_matches) == 1:
                return partial_matches[0]
        return None
