from typing import Any

from reminder_agent.application import process_request
from tests.fakes import FakeProvider


def test_explicit_create_returns_proposed_action() -> None:
    provider = FakeProvider(
        {
            "status": "action",
            "action": {
                "kind": "create",
                "task": "Submit assignment",
                "date": "2026-11-20",
                "time": "09:00",
                "timezone": None,
            },
        }
    )
    request: dict[str, Any] = {
        "request": "Remind me to submit my assignment on 2026-11-20 at 9 AM"
    }

    response = process_request(request, provider)

    assert response["action"]["kind"] == "create"
    assert response["action"]["task"] == "Submit assignment"
    assert "target_reminder_id" not in response["action"]


def test_missing_schedule_is_clarified_without_provider_action() -> None:
    provider = FakeProvider(
        {
            "status": "action",
            "action": {
                "kind": "create",
                "task": "Submit assignment",
                "date": "2026-11-20",
                "time": "09:00",
                "timezone": None,
            },
        }
    )

    response = process_request({"request": "Remind me to submit my assignment"}, provider)

    assert response["status"] == "clarification"
    assert response["action"] is None
    assert provider.calls == 0


def test_relative_create_resolves_from_supplied_context() -> None:
    provider = FakeProvider(
        {
            "status": "action",
            "action": {
                "kind": "create",
                "task": "Submit assignment",
                "date": "2026-11-13",
                "time": "09:00",
                "timezone": "Asia/Kolkata",
            },
        }
    )
    request = {
        "request": "Remind me to submit my assignment tomorrow at 9 AM",
        "reference_context": {
            "current_datetime": "2026-11-12T10:00:00+05:30",
            "timezone": "Asia/Kolkata",
        },
    }

    response = process_request(request, provider)

    assert response["action"]["date"] == "2026-11-13"
    assert response["action"]["timezone"] == "Asia/Kolkata"
