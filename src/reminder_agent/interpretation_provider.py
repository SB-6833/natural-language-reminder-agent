"""Provider-neutral interface for live reminder interpretation."""

from __future__ import annotations

import importlib
import os
from typing import Any, Protocol


class ReminderProvider(Protocol):
    def interpret(self, request: dict[str, Any]) -> dict[str, Any] | str:
        """Return a structured response candidate for the supplied request."""


class MissingProviderError(RuntimeError):
    """Raised when a live interpretation provider has not been configured."""


class ProviderConfigurationError(RuntimeError):
    """Raised when the configured provider plugin cannot be loaded."""


def load_provider_from_environment() -> ReminderProvider:
    """Load a user-selected provider factory from REMINDER_AGENT_PROVIDER."""
    spec = os.environ.get("REMINDER_AGENT_PROVIDER", "").strip()
    if not spec:
        raise MissingProviderError(
            "No interpretation provider is configured. Set REMINDER_AGENT_PROVIDER "
            "to a project-approved module:factory before running live requests."
        )
    module_name, separator, factory_name = spec.partition(":")
    if not separator or not module_name or not factory_name:
        raise ProviderConfigurationError(
            "REMINDER_AGENT_PROVIDER must use the form 'module:factory'."
        )
    try:
        module = importlib.import_module(module_name)
        factory = getattr(module, factory_name)
    except (ImportError, AttributeError) as error:
        raise ProviderConfigurationError(
            "The configured interpretation provider could not be loaded."
        ) from error
    if not callable(factory):
        raise ProviderConfigurationError(
            "The configured interpretation provider factory is not callable."
        )
    provider = factory()
    if not callable(getattr(provider, "interpret", None)):
        raise ProviderConfigurationError(
            "The configured provider must expose an interpret(request) method."
        )
    return provider
