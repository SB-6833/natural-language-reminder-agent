"""Validation for reviewer-supplied semantic rubric assessments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from reminder_agent.validation import validate_semantic_assessment


class AssessmentError(ValueError):
    """Raised when semantic assessments are missing, malformed, or inconsistent."""


DIMENSIONS = (
    "intent",
    "task_target_identification",
    "schedule_interpretation",
    "clarification_rejection_correctness",
    "unsupported_assumptions",
)


def load_assessments(path: str | Path) -> list[dict[str, Any]]:
    assessments: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        with Path(path).open(encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as error:
                    errors.append(f"line {line_number}: invalid JSON ({error.msg})")
                    continue
                schema_errors = validate_semantic_assessment(item)
                if schema_errors:
                    errors.append(
                        f"line {line_number}: " + "; ".join(schema_errors)
                    )
                    continue
                assessments.append(item)
    except OSError as error:
        raise AssessmentError(f"Unable to read semantic assessments: {error}") from error
    if errors:
        raise AssessmentError("; ".join(errors))
    return assessments


def validate_assessments(
    assessments: Iterable[dict[str, Any]],
    expected_case_ids: Iterable[str],
    evaluator_method: str,
) -> dict[str, dict[str, Any]]:
    expected = set(expected_case_ids)
    indexed: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for index, assessment in enumerate(assessments, start=1):
        schema_errors = validate_semantic_assessment(assessment)
        if schema_errors:
            errors.append(f"assessment {index}: " + "; ".join(schema_errors))
            continue
        case_id = assessment["case_id"]
        if case_id not in expected:
            errors.append(f"assessment {index}: unknown case_id {case_id}")
        if case_id in indexed:
            errors.append(f"assessment {index}: duplicate case_id {case_id}")
        else:
            indexed[case_id] = assessment
        if assessment["evaluator_method"] != evaluator_method:
            errors.append(
                f"assessment {index}: evaluator_method does not match the run"
            )
    missing = expected - indexed.keys()
    if missing:
        errors.append("missing assessments for: " + ", ".join(sorted(missing)))
    if errors:
        raise AssessmentError("; ".join(errors))
    return indexed
