from reminder_agent.application import process_request
from tests.fakes import FakeProvider


def test_reschedule_uses_exact_matching_record() -> None:
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


def test_snooze_uses_supplied_record_and_reference_datetime() -> None:
    provider = FakeProvider(
        {
            "status": "action",
            "action": {
                "kind": "snooze",
                "target_reminder_id": "rem-43",
                "task": "Submit assignment",
                "date": "2026-11-12",
                "time": "12:00",
                "timezone": "Asia/Kolkata",
            },
        }
    )
    request = {
        "request": "Snooze my assignment reminder for 2 hours",
        "reference_context": {
            "current_datetime": "2026-11-12T10:00:00+05:30",
            "timezone": "Asia/Kolkata",
        },
        "existing_reminders": [
            {
                "reminder_id": "rem-43",
                "task": "Submit assignment",
                "date": "2026-11-12",
                "time": "10:00",
                "timezone": "Asia/Kolkata",
            }
        ],
    }

    response = process_request(request, provider)

    assert response["action"]["target_reminder_id"] == "rem-43"
    assert response["action"]["date"] == "2026-11-12"
    assert response["action"]["time"] == "12:00"


def test_duplicate_ids_require_clarification_without_provider_call() -> None:
    provider = FakeProvider({})
    request = {
        "request": "Snooze my dentist reminder for 2 hours",
        "reference_context": {
            "current_datetime": "2026-11-12T10:00:00+05:30",
            "timezone": "Asia/Kolkata",
        },
        "existing_reminders": [
            {
                "reminder_id": "rem-61",
                "task": "Call the dentist",
                "date": "2026-11-12",
                "time": "10:00",
                "timezone": "Asia/Kolkata",
            },
            {
                "reminder_id": "rem-61",
                "task": "Visit the dentist",
                "date": "2026-11-12",
                "time": "11:00",
                "timezone": "Asia/Kolkata",
            },
        ],
    }

    response = process_request(request, provider)

    assert response["status"] == "clarification"
    assert response["action"] is None
    assert provider.calls == 0


def test_multiple_matching_reminders_require_clarification() -> None:
    provider = FakeProvider({})
    request = {
        "request": "Move my doctor reminder to 2026-11-20 at 15:00",
        "existing_reminders": [
            {
                "reminder_id": "rem-51",
                "task": "Call the doctor",
                "date": "2026-11-19",
                "time": "10:00",
                "timezone": None,
            },
            {
                "reminder_id": "rem-52",
                "task": "Visit the doctor",
                "date": "2026-11-19",
                "time": "11:00",
                "timezone": None,
            },
        ],
    }

    response = process_request(request, provider)

    assert response["status"] == "clarification"
    assert response["action"] is None
    assert provider.calls == 0
