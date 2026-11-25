from typing import Any, Protocol


class AssistantProvider(Protocol):
    """Stable boundary for deterministic and future model-backed assistants."""

    def generate_response(
        self, question: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Return Markdown content and structured UI metadata."""
        ...
