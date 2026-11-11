"""Deterministic contract and reminder-safety validation."""

from __future__ import annotations

import copy
import json
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator, FormatChecker


CONTRACTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "001-natural-language-reminders"
    / "contracts"
)

_SCHEMA_FILES = {
    "request": "reminder-request.schema.json",
    "response": "reminder-response.schema.json",
    "evaluation_case": "evaluation-case.schema.json",
    "semantic_assessment": "semantic-assessment.schema.json",
}

_STOP_WORDS = {
    "a", "an", "and", "at", "by", "for", "from", "i", "me", "my", "of",
    "on", "please", "remind", "reminder", "the", "to", "with", "move",
    "reschedule", "snooze", "postpone", "change", "set", "create", "add",
    "tomorrow", "today", "next", "this", "in", "am", "pm",
}
_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def load_schema(name: str) -> dict[str, Any]:
    """Load one documented JSON Schema contract."""
    try:
        filename = _SCHEMA_FILES[name]
    except KeyError as error:
        raise ValueError(f"Unknown contract name: {name}") from error
    path = CONTRACTS_DIR / filename
    with path.open(encoding="utf-8") as file:
        schema = json.load(file)
    if name == "evaluation_case":
        request_schema = load_schema("request")
        schema = copy.deepcopy(schema)
        schema["$defs"] = request_schema.get("$defs", {})
        schema["properties"]["input"] = request_schema
    return schema


def _schema_errors(instance: Any, schema_name: str) -> list[str]:
    validator = Draft202012Validator(
        load_schema(schema_name),
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: "
        f"{error.message}"
        for error in errors
    ]


def _valid_timezone(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or not value:
        return False
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        return False
    return True


def validate_request(request: Any) -> list[str]:
    errors = _schema_errors(request, "request")
    if not isinstance(request, dict):
        return errors

    reference = request.get("reference_context")
    if isinstance(reference, dict) and not _valid_timezone(reference.get("timezone")):
        errors.append("reference_context.timezone must be a valid IANA identifier or null")

    reminders = request.get("existing_reminders", [])
    if isinstance(reminders, list):
        seen: set[str] = set()
        for index, reminder in enumerate(reminders):
            if not isinstance(reminder, dict):
                continue
            reminder_id = reminder.get("reminder_id")
            if isinstance(reminder_id, str):
                if reminder_id in seen:
                    errors.append(
                        f"existing_reminders[{index}].reminder_id must be unique"
                    )
                seen.add(reminder_id)
            if not _valid_timezone(reminder.get("timezone")):
                errors.append(
                    f"existing_reminders[{index}].timezone must be a valid IANA "
                    "identifier or null"
                )
    return errors


def validate_response(response: Any) -> list[str]:
    return _schema_errors(response, "response")


def validate_evaluation_case(case: Any) -> list[str]:
    return _schema_errors(case, "evaluation_case")


def validate_semantic_assessment(assessment: Any) -> list[str]:
    return _schema_errors(assessment, "semantic_assessment")


def classify_intent(text: str) -> str | None:
    lowered = text.lower()
    if re.search(r"\b(snooze|snoozed)\b", lowered):
        return "snooze"
    if re.search(r"\b(reschedule|move|postpone|push back|change)\b", lowered):
        return "reschedule"
    if re.search(r"\b(remind me|set (?:a )?reminder|create (?:a )?reminder|"
                 r"add (?:a )?reminder)\b", lowered):
        return "create"
    return None


def _reference_datetime(request: dict[str, Any]) -> datetime | None:
    context = request.get("reference_context")
    if not isinstance(context, dict):
        return None
    value = context.get("current_datetime")
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _extract_dates(text: str, request: dict[str, Any]) -> tuple[set[str], bool]:
    dates: set[str] = set()
    ambiguous = False
    for raw in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text):
        try:
            dates.add(date.fromisoformat(raw).isoformat())
        except ValueError:
            ambiguous = True

    reference = _reference_datetime(request)
    lowered = text.lower()
    if re.search(r"\btoday\b", lowered):
        if reference is None:
            ambiguous = True
        else:
            dates.add(reference.date().isoformat())
    if re.search(r"\btomorrow\b", lowered):
        if reference is None:
            ambiguous = True
        else:
            dates.add((reference.date() + timedelta(days=1)).isoformat())

    duration = re.search(r"\bin\s+(\d+)\s+days?\b", lowered)
    if duration:
        if reference is None:
            ambiguous = True
        else:
            dates.add(
                (reference.date() + timedelta(days=int(duration.group(1)))).isoformat()
            )

    for weekday, weekday_number in _WEEKDAYS.items():
        if re.search(rf"\b(?:next|this|on)?\s*{weekday}\b", lowered):
            if reference is None:
                ambiguous = True
                continue
            offset = (weekday_number - reference.weekday()) % 7
            if offset == 0:
                offset = 7
            dates.add((reference.date() + timedelta(days=offset)).isoformat())

    if re.search(r"\b(?:or|either)\b", lowered) and (
        re.search(r"\b(?:today|tomorrow|next\s+\w+|on\s+\w+day)\b", lowered)
    ):
        ambiguous = True
    if len(dates) > 1:
        ambiguous = True
    return dates, ambiguous


def _extract_times(text: str) -> tuple[set[str], bool]:
    times: set[str] = set()
    ambiguous = False
    lowered = text.lower()
    if re.search(r"\bmidnight\b", lowered):
        times.add("00:00")
    if re.search(r"\bnoon\b", lowered):
        times.add("12:00")

    for match in re.finditer(
        r"\b(\d{1,2})(?::([0-5]\d))?\s*(a\.?m\.?|p\.?m\.?)\b",
        lowered,
    ):
        hour = int(match.group(1))
        minute = int(match.group(2) or "00")
        meridiem = match.group(3).replace(".", "")
        if not 1 <= hour <= 12:
            ambiguous = True
            continue
        hour = hour % 12 + (12 if meridiem == "pm" else 0)
        times.add(f"{hour:02d}:{minute:02d}")

    for match in re.finditer(r"\b([01]\d|2[0-3]):([0-5]\d)\b", lowered):
        times.add(f"{int(match.group(1)):02d}:{match.group(2)}")

    if re.search(
        r"\bat\s+\d{1,2}\b(?!\s*(?::\d{2}|a\.?m\.?|p\.?m\.?))",
        lowered,
    ):
        ambiguous = True
    if len(times) > 1:
        ambiguous = True
    return times, ambiguous


def _snooze_datetime(request: dict[str, Any]) -> datetime | None:
    text = request.get("request", "").lower()
    match = re.search(r"\bfor\s+(\d+)\s+(minutes?|hours?|days?)\b", text)
    reference = _reference_datetime(request)
    if not match or reference is None:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    if unit.startswith("minute"):
        return reference + timedelta(minutes=amount)
    if unit.startswith("hour"):
        return reference + timedelta(hours=amount)
    return reference + timedelta(days=amount)


def schedule_evidence(request: dict[str, Any], intent: str) -> tuple[set[str], set[str], bool]:
    text = request.get("request", "")
    dates, date_ambiguous = _extract_dates(text, request)
    times, time_ambiguous = _extract_times(text)
    snooze_at = _snooze_datetime(request) if intent == "snooze" else None
    if snooze_at is not None:
        dates.add(snooze_at.date().isoformat())
        times.add(snooze_at.strftime("%H:%M"))
    return dates, times, date_ambiguous or time_ambiguous or len(dates) > 1 or len(times) > 1


def _words(text: str) -> set[str]:
    return {
        word for word in re.findall(r"[a-z0-9]+", text.lower())
        if word not in _STOP_WORDS
    }


def match_update_target(request: dict[str, Any]) -> dict[str, Any] | None:
    text = request.get("request", "").lower()
    reminders = request.get("existing_reminders", [])
    ids = [
        item.get("reminder_id", "").lower()
        for item in reminders
        if isinstance(item.get("reminder_id"), str)
        and re.search(
            rf"(?<![\w-]){re.escape(item.get('reminder_id', '').lower())}(?![\w-])",
            text,
        )
    ]
    if ids:
        matches = [item for item in reminders if item.get("reminder_id", "").lower() in ids]
        return matches[0] if len(matches) == 1 else None

    request_words = _words(text)
    scores = [
        (len(request_words & _words(item.get("task", ""))), item)
        for item in reminders
    ]
    scores = [(score, item) for score, item in scores if score > 0]
    if not scores:
        return None
    highest = max(score for score, _ in scores)
    winners = [item for score, item in scores if score == highest]
    return winners[0] if len(winners) == 1 else None


def _request_task_text(text: str) -> str:
    match = re.search(r"\bremind me to\s+(.+)", text, re.IGNORECASE)
    if not match:
        return ""
    task = match.group(1)
    task = re.split(
        r"\b(?:on|at|tomorrow|today|next\s+\w+|this\s+\w+|in\s+\d+\s+days?)\b",
        task,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return task.strip(" .,!?:")


def preflight_response(request: Any) -> dict[str, Any] | None:
    request_errors = validate_request(request)
    if request_errors:
        if isinstance(request, dict) and any(
            "existing_reminders" in error or "reference_context" in error
            for error in request_errors
        ):
            return {
                "status": "clarification",
                "action": None,
                "questions": [
                    "The supplied reminder or reference context is invalid. Please clarify the required context."
                ],
            }
        return {
            "status": "rejected",
            "action": None,
            "reason": "The request or supplied reminder context is invalid.",
        }
    text = request["request"]
    lowered = text.lower()
    if re.search(
        r"\b(ignore|bypass|override)\b.{0,50}\b(safety|rules?|instructions?|schema|format)\b",
        lowered,
    ) or re.search(r"\binvent\b.{0,30}\b(date|time|reminder)\b", lowered):
        return {
            "status": "rejected",
            "action": None,
            "reason": "The request attempts to bypass reminder safety requirements.",
        }
    intent = classify_intent(text)
    if intent is None:
        return {
            "status": "rejected",
            "action": None,
            "reason": "The input is not a sufficiently clear reminder request.",
        }

    if intent == "create" and not _request_task_text(text):
        return {
            "status": "clarification",
            "action": None,
            "questions": ["What task should the reminder be for?"],
        }

    target = None
    if intent in {"reschedule", "snooze"}:
        target = match_update_target(request)
        if target is None:
            return {
                "status": "clarification",
                "action": None,
                "questions": ["Which existing reminder do you mean? Please identify it by task or reminder ID."],
            }

    dates, times, ambiguous = schedule_evidence(request, intent)
    if ambiguous:
        return {
            "status": "clarification",
            "action": None,
            "questions": ["Please clarify the intended date and time."],
        }
    snooze_at = _snooze_datetime(request) if intent == "snooze" else None
    if intent == "create" and (not dates or not times):
        missing = "date" if not dates else "time"
        return {
            "status": "clarification",
            "action": None,
            "questions": [f"What {missing} should I use for the reminder?"],
        }
    if intent in {"reschedule", "snooze"} and not dates and not times and snooze_at is None:
        return {
            "status": "clarification",
            "action": None,
            "questions": ["What new date or time should I use?"],
        }
    return None


def behavioral_violations(
    request: dict[str, Any],
    response: dict[str, Any],
) -> list[str]:
    if response["status"] != "action":
        return []
    action = response["action"]
    intent = classify_intent(request["request"])
    errors: list[str] = []
    if action["kind"] != intent:
        errors.append("action kind does not match request intent")

    dates, times, _ = schedule_evidence(request, intent or "")
    if action["kind"] == "create":
        task_words = _words(action["task"])
        request_words = _words(_request_task_text(request["request"]))
        if not task_words or not task_words.issubset(request_words):
            errors.append("create task contains unsupported details")
        if dates and action["date"] not in dates:
            errors.append("create date is not supported by the request or context")
        if times and action["time"] not in times:
            errors.append("create time is not supported by the request")
        context = request.get("reference_context", {})
        supplied_timezone = context.get("timezone") if isinstance(context, dict) else None
        if action["timezone"] != supplied_timezone:
            errors.append("create time zone must match supplied context or remain null")
        return errors

    target = match_update_target(request)
    if target is None:
        errors.append("update target is not uniquely identified")
        return errors
    if action["target_reminder_id"] != target["reminder_id"]:
        errors.append("update target ID does not match the identified record")
    if action["task"] != target["task"]:
        errors.append("update task does not match the identified record")
    expected_date = next(iter(dates), target["date"])
    expected_time = next(iter(times), target["time"])
    snooze_at = _snooze_datetime(request) if intent == "snooze" else None
    if snooze_at is not None:
        expected_date = snooze_at.date().isoformat()
        expected_time = snooze_at.strftime("%H:%M")
    if action["date"] != expected_date:
        errors.append("update date is unsupported or differs from the matched record")
    if action["time"] != expected_time:
        errors.append("update time is unsupported or differs from the matched record")
    context = request.get("reference_context", {})
    requested_timezone = context.get("timezone") if isinstance(context, dict) else None
    expected_timezone = requested_timezone or target.get("timezone")
    if action["timezone"] != expected_timezone:
        errors.append("update time zone is unsupported or differs from the matched record")
    return errors


def evaluation_behavioral_violations(
    request: dict[str, Any],
    response: dict[str, Any],
    expected: dict[str, Any],
) -> tuple[list[str], bool]:
    """Compare deterministic safety invariants and expected case outcome."""
    errors = behavioral_violations(request, response)
    critical_failure = bool(errors)
    if response["status"] != expected["outcome"]:
        errors.append("response outcome does not match the evaluation case")
        critical_failure = critical_failure or (
            response["status"] == "action"
            and expected["outcome"] != "action"
        )
    if response["status"] == "action":
        action = response["action"]
        if action["kind"] != expected["intent"]:
            errors.append("action kind does not match the expected case intent")
            critical_failure = True
        expected_target_id = expected["target_reminder_id"]
        if (
            expected_target_id is not None
            and action.get("target_reminder_id") != expected_target_id
        ):
            errors.append("target ID does not match the expected case target")
            critical_failure = True
    return errors, critical_failure
