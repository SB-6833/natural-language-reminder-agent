import json

from reminder_agent.evaluation import EvaluationRunner
from tests.fakes import FakeProvider


def test_prepare_resume_and_human_decision_preserve_run_evidence(tmp_path) -> None:
    case = {
        "case_id": "C01",
        "category": "normal",
        "input": {
            "request": "Remind me to submit assignment on 2026-11-20 at 09:00"
        },
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
    dataset.write_text(json.dumps(case) + "\n", encoding="utf-8")
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
    runner = EvaluationRunner(provider, tmp_path / "artifacts")

    prepared = runner.prepare(dataset, phase="initial", semantic_method="rubric_based")
    before = (tmp_path / "artifacts" / "initial" / prepared["run_id"] / "responses.jsonl").read_text(
        encoding="utf-8"
    )
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
    assessments = tmp_path / "assessments.jsonl"
    assessments.write_text(json.dumps(assessment) + "\n", encoding="utf-8")

    final = runner.resume(
        prepared["run_id"],
        dataset,
        assessments,
        phase="initial",
        semantic_method="rubric_based",
    )
    after = (tmp_path / "artifacts" / "initial" / prepared["run_id"] / "responses.jsonl").read_text(
        encoding="utf-8"
    )
    decision = runner.record_human_decision(
        prepared["run_id"], "ACCEPT", "The evaluation satisfies the acceptance criteria."
    )
    initial_evidence = {
        name: (tmp_path / "artifacts" / "initial" / prepared["run_id"] / name).read_bytes()
        for name in ("cases.jsonl", "responses.jsonl", "reviewer-packet.jsonl", "report.json")
    }
    post_repair = runner.prepare(
        dataset,
        phase="post-repair",
        semantic_method="rubric_based",
    )

    assert prepared["status"] == "PENDING_ASSESSMENT"
    assert provider.calls == 2
    assert before == after
    assert final["status"] in {"PASS", "FAIL"}
    assert final["checks"] == ["structural", "behavioral", "semantic"]
    assert final["case_results"][0]["scores"]["intent"] == 2
    assert final["case_results"][0]["reasons"]["unsupported_assumptions"]
    assert post_repair["run_id"] != prepared["run_id"]
    assert all(
        (tmp_path / "artifacts" / "initial" / prepared["run_id"] / name).read_bytes()
        == original
        for name, original in initial_evidence.items()
    )
    assert decision["decision"] == "ACCEPT"
    assert decision["rationale"]
    assert decision["decision_timestamp"]
    assert decision["evaluation_run_id"] == prepared["run_id"]


def test_missing_assessment_file_fails_final_evaluation(tmp_path) -> None:
    case = {
        "case_id": "C01",
        "category": "normal",
        "input": {
            "request": "Remind me to submit assignment on 2026-11-20 at 09:00"
        },
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
    dataset.write_text(json.dumps(case) + "\n", encoding="utf-8")
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
    runner = EvaluationRunner(provider, tmp_path / "artifacts")
    prepared = runner.prepare(dataset, phase="initial", semantic_method="rubric_based")

    final = runner.resume(
        prepared["run_id"],
        dataset,
        tmp_path / "missing-assessments.jsonl",
        phase="initial",
        semantic_method="rubric_based",
    )

    assert final["status"] == "FAIL"
    assert final["assessment_errors"]
    assert provider.calls == 1

    invalid_assessments = tmp_path / "invalid-assessments.jsonl"
    invalid_assessments.write_text('{"case_id":"C01"}\n', encoding="utf-8")
    invalid_final = runner.resume(
        prepared["run_id"],
        dataset,
        invalid_assessments,
        phase="initial",
        semantic_method="rubric_based",
    )

    assert invalid_final["status"] == "FAIL"
    assert invalid_final["assessment_errors"]
    assert provider.calls == 1


def test_unsupported_assumption_zero_fails_high_aggregate_pipeline(tmp_path) -> None:
    case = {
        "case_id": "C01",
        "category": "normal",
        "input": {
            "request": "Remind me to submit assignment on 2026-11-20 at 09:00"
        },
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
    dataset.write_text(json.dumps(case) + "\n", encoding="utf-8")
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
    runner = EvaluationRunner(provider, tmp_path / "artifacts")
    prepared = runner.prepare(dataset, phase="initial", semantic_method="rubric_based")
    assessment = {
        "case_id": "C01",
        "evaluator_method": "rubric_based",
        "scores": {
            "intent": 2,
            "task_target_identification": 2,
            "schedule_interpretation": 2,
            "clarification_rejection_correctness": 2,
            "unsupported_assumptions": 0,
        },
        "reasons": {
            "intent": "Correct intent.",
            "task_target_identification": "Correct task.",
            "schedule_interpretation": "Correct schedule.",
            "clarification_rejection_correctness": "Correct outcome.",
            "unsupported_assumptions": "An unsupported assumption was present.",
        },
    }
    assessments = tmp_path / "assessments.jsonl"
    assessments.write_text(json.dumps(assessment) + "\n", encoding="utf-8")

    final = runner.resume(
        prepared["run_id"],
        dataset,
        assessments,
        phase="initial",
        semantic_method="rubric_based",
    )

    assert final["scores"]["aggregate_score"] >= 90
    assert final["status"] == "FAIL"
    assert final["scores"]["critical_failures"] == ["C01"]
