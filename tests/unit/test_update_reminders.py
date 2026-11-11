from reminder_agent.application import process_request
from reminder_agent.validation import validate_request
from tests.fakes import FakeProvider


def test_duplicate_existing_reminder_ids_are_invalid() -> None:
    request = {
        "request": "Move my doctor reminder to 2026-11-20 at 15:00",
        "existing_reminders": [
            {
                "reminder_id": "rem-1",
                "task": "Call doctor",
                "date": "2026-11-19",
                "time": "10:00",
                "timezone": None,
            },
            {
                "reminder_id": "rem-1",
                "task": "Visit doctor",
                "date": "2026-11-19",
                "time": "11:00",
                "timezone": None,
            },
        ],
    }

    assert validate_request(request)


def test_update_uses_exact_unique_target_id_and_task() -> None:
    provider = FakeProvider(
        {
            "status": "action",
            "action": {
                "kind": "reschedule",
                "target_reminder_id": "rem-42",
                "task": "Call the doctor",
                "date": "2026-11-20",
                "time": "15:00",
                "timezone": "Asia/Kolkata",
            },
        }
    )
    request = {
        "request": "Move my doctor reminder to 2026-11-20 at 3 PM",
        "reference_context": {
            "current_datetime": "2026-11-12T10:00:00+05:30",
            "timezone": "Asia/Kolkata",
        },
        "existing_reminders": [
            {
                "reminder_id": "rem-42",
                "task": "Call the doctor",
                "date": "2026-11-19",
                "time": "10:00",
                "timezone": "Asia/Kolkata",
            }
        ],
    }

    response = process_request(request, provider)

    assert response["action"]["target_reminder_id"] == "rem-42"
    assert response["action"]["task"] == "Call the doctor"


def test_single_record_without_request_reference_still_clarifies() -> None:
    provider = FakeProvider(
        {
            "status": "action",
            "action": {
                "kind": "reschedule",
                "target_reminder_id": "rem-42",
                "task": "Call doctor",
                "date": "2026-11-20",
                "time": "15:00",
                "timezone": None,
            },
        }
    )
    request = {
        "request": "Move my reminder to 2026-11-20 at 3 PM",
        "existing_reminders": [
            {
                "reminder_id": "rem-42",
                "task": "Call doctor",
                "date": "2026-11-19",
                "time": "10:00",
                "timezone": None,
            }
        ],
    }

    response = process_request(request, provider)

    assert response["status"] == "clarification"
    assert response["action"] is None
    assert provider.calls == 0


def test_id_prefix_does_not_match_a_longer_reminder_id() -> None:
    provider = FakeProvider({})
    response = process_request(
        {
            "request": "Move rem-4 to 2026-11-20 at 3 PM",
            "existing_reminders": [
                {
                    "reminder_id": "rem-42",
                    "task": "Call doctor",
                    "date": "2026-11-19",
                    "time": "10:00",
                    "timezone": None,
                }
            ],
        },
        provider,
    )

    assert response["status"] == "clarification"
    assert response["action"] is None
    assert provider.calls == 0
