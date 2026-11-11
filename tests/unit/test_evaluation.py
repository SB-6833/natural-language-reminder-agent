import json

import pytest

from reminder_agent.evaluation import calculate_scores, load_dataset
from reminder_agent.semantic_assessment import AssessmentError, validate_assessments
from reminder_agent.validation import evaluation_behavioral_violations


def test_dataset_lines_are_independently_validated(tmp_path) -> None:
    valid_case = {
        "case_id": "C01",
        "category": "normal",
        "input": {"request": "Remind me to submit assignment on 2026-11-20 at 09:00"},
        "expected": {
            "outcome": "action",
            "intent": "create",
            "task_meaning": "submit assignment",
            "target_reminder_id": None,
            "date": "2026-11-20",
            "time": "09:00",
            "timezone": None,
            "clarification_topic": None,
            "semantic_reference": "Create a submission reminder.",
            "critical_safety_case": False,
        },
    }
    dataset = tmp_path / "cases.jsonl"
    dataset.write_text(json.dumps(valid_case) + "\n" + '{"invalid": true}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="line 2"):
        load_dataset(dataset)


def test_assessments_require_exact_case_ids_and_all_dimensions() -> None:
    assessment = {
        "case_id": "C01",
        "evaluator_method": "rubric_based",
        "scores": {
            "intent": 2,
            "task_target_identification": 2,
            "schedule_interpretation": 2,
            "clarification_rejection_correctness": 2,
            "unsupported_assumptions": 2,
        },
        "reasons": {
            "intent": "Correct intent.",
            "task_target_identification": "Correct task.",
            "schedule_interpretation": "Correct schedule.",
            "clarification_rejection_correctness": "Correct outcome.",
            "unsupported_assumptions": "No unsupported detail.",
        },
    }

    assert validate_assessments([assessment], ["C01"], "rubric_based") == {"C01": assessment}
    with pytest.raises(AssessmentError):
        validate_assessments([], ["C01"], "rubric_based")


def test_unsupported_assumption_zero_fails_even_with_high_aggregate() -> None:
    cases = [
        {
            "case_id": "C01",
            "structural_pass": True,
            "behavioral_pass": True,
            "critical_failure": False,
            "scores": {
                "intent": 2,
                "task_target_identification": 2,
                "schedule_interpretation": 2,
                "clarification_rejection_correctness": 2,
                "unsupported_assumptions": 0,
            },
        }
    ]

    result = calculate_scores(cases)

    assert result["aggregate_score"] >= 90
    assert result["status"] == "FAIL"
    assert result["critical_failures"]


def test_maintained_dataset_has_twenty_independently_valid_cases() -> None:
    from pathlib import Path

    dataset = Path(__file__).resolve().parents[2] / "data" / "evaluation_cases.jsonl"

    cases = load_dataset(dataset)

    assert len(cases) >= 20
    assert {
        "normal",
        "boundary",
        "ambiguous",
        "missing_information",
        "malformed",
        "adversarial",
    }.issubset({case["category"] for case in cases})


def test_unexpected_action_for_non_action_case_is_critical() -> None:
    request = {"request": "What is the weather today?"}
    response = {
        "status": "action",
        "action": {
            "kind": "create",
            "task": "Check weather",
            "date": "2026-11-20",
            "time": "09:00",
            "timezone": None,
        },
    }
    expected = {
        "outcome": "rejected",
        "intent": "none",
        "target_reminder_id": None,
    }

    errors, critical = evaluation_behavioral_violations(request, response, expected)

    assert errors
    assert critical
