"""Request dispatch and safe response handling."""

from __future__ import annotations

import json
from typing import Any

from reminder_agent.interpretation_provider import MissingProviderError, ReminderProvider
from reminder_agent.validation import (
    behavioral_violations,
    preflight_response,
    validate_response,
)


class ProviderResponseError(RuntimeError):
    """Raised when provider output cannot safely become an application response."""


class InvalidProviderOutputError(ProviderResponseError):
    """Raised when provider output is not valid JSON matching the response schema."""


class UnsafeProviderResponseError(ProviderResponseError):
    """Raised when a schema-valid provider response violates safety invariants."""


def process_request(
    request: Any,
    provider: ReminderProvider | None,
) -> dict[str, Any]:
    """Validate a request, call the provider, and return only a safe response."""
    safe_outcome = preflight_response(request)
    if safe_outcome is not None:
        return safe_outcome
    if provider is None:
        raise MissingProviderError(
            "No interpretation provider was supplied for this reminder request."
        )

    candidate = provider.interpret(request)
    if isinstance(candidate, str):
        try:
            candidate = json.loads(candidate)
        except json.JSONDecodeError as error:
            raise InvalidProviderOutputError(
                "The interpretation provider returned invalid JSON."
            ) from error
    if not isinstance(candidate, dict):
        raise InvalidProviderOutputError(
            "The interpretation provider response must be a JSON object."
        )

    schema_errors = validate_response(candidate)
    if schema_errors:
        raise InvalidProviderOutputError(
            "The interpretation provider response failed schema validation: "
            + "; ".join(schema_errors)
        )
    behavior_errors = behavioral_violations(request, candidate)
    if behavior_errors:
        raise UnsafeProviderResponseError(
            "The interpretation provider response failed safety validation: "
            + "; ".join(behavior_errors)
        )
    return candidate
