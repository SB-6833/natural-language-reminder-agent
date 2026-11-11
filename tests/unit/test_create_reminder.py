from reminder_agent.validation import validate_response


def test_create_action_requires_schedule_and_forbids_target_id() -> None:
    valid = {
        "status": "action",
        "action": {
            "kind": "create",
            "task": "Submit assignment",
            "date": "2026-11-20",
            "time": "09:00",
            "timezone": None,
        },
    }
    invalid = {
        "status": "action",
        "action": {**valid["action"], "target_reminder_id": "rem-1"},
    }

    assert validate_response(valid) == []
    assert validate_response({**valid, "action": {"kind": "create"}})
    assert validate_response(invalid)


def test_update_action_requires_target_id() -> None:
    response = {
        "status": "action",
        "action": {
            "kind": "snooze",
            "task": "Call doctor",
            "date": "2026-11-13",
            "time": "09:00",
            "timezone": None,
        },
    }

    assert validate_response(response)
