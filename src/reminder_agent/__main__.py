"""JSON stdin/stdout application entry point."""

from __future__ import annotations

import json
import sys

from reminder_agent.application import ProviderResponseError, process_request
from reminder_agent.interpretation_provider import (
    MissingProviderError,
    ProviderConfigurationError,
    load_provider_from_environment,
)


def main() -> int:
    try:
        request = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"Invalid request JSON: {error.msg}", file=sys.stderr)
        return 2
    try:
        try:
            response = process_request(request, None)
        except MissingProviderError:
            provider = load_provider_from_environment()
            response = process_request(request, provider)
    except (MissingProviderError, ProviderConfigurationError, ProviderResponseError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
