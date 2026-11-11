"""Single-run evaluation, reviewer assessment, and evidence handling."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reminder_agent.application import (
    InvalidProviderOutputError,
    UnsafeProviderResponseError,
    process_request,
)
from reminder_agent.interpretation_provider import ReminderProvider
from reminder_agent.semantic_assessment import (
    AssessmentError,
    load_assessments,
    validate_assessments,
)
from reminder_agent.validation import (
    evaluation_behavioral_violations,
    validate_evaluation_case,
    validate_response,
)


THRESHOLDS = {
    "structural_validity_percent": 100,
    "behavioral_correctness_percent": 90,
    "semantic_quality_percent": 80,
    "aggregate_percent": 90,
}
WEIGHTS = {
    "structural_validity": 0.4,
    "behavioral_correctness": 0.4,
    "semantic_quality": 0.2,
}


def load_dataset(path: str | Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    errors: list[str] = []
    with Path(path).open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            try:
                case = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(f"line {line_number}: invalid JSON ({error.msg})")
                continue
            schema_errors = validate_evaluation_case(case)
            if schema_errors:
                case_id = case.get("case_id") if isinstance(case, dict) else None
                label = f" case_id {case_id}" if case_id else ""
                errors.append(
                    f"line {line_number}{label}: " + "; ".join(schema_errors)
                )
                continue
            cases.append(case)
    if errors:
        raise ValueError("Invalid evaluation dataset: " + "; ".join(errors))
    if not cases:
        raise ValueError("The evaluation dataset contains no cases.")
    ids = [case["case_id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("The evaluation dataset contains duplicate case IDs.")
    return cases


def calculate_scores(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not case_results:
        raise ValueError("Cannot calculate evaluation scores without cases.")
    count = len(case_results)
    structural = sum(bool(case.get("structural_pass")) for case in case_results)
    behavioral = sum(bool(case.get("behavioral_pass")) for case in case_results)
    structural_percent = structural / count * 100
    behavioral_percent = behavioral / count * 100
    assessments = [case.get("scores") for case in case_results]
    if any(scores is None for scores in assessments):
        return {
            "status": "PENDING_ASSESSMENT",
            "structural_validity_percent": structural_percent,
            "behavioral_correctness_percent": behavioral_percent,
            "semantic_quality_percent": None,
            "aggregate_score": None,
            "critical_failures": [
                case["case_id"]
                for case in case_results
                if case.get("critical_failure")
            ],
        }

    possible = count * 10
    earned = sum(
        sum(int(score) for score in scores.values())
        for scores in assessments
    )
    semantic_percent = earned / possible * 100
    aggregate = (
        structural_percent * WEIGHTS["structural_validity"]
        + behavioral_percent * WEIGHTS["behavioral_correctness"]
        + semantic_percent * WEIGHTS["semantic_quality"]
    )
    critical_failures = [
        case["case_id"]
        for case in case_results
        if case.get("critical_failure")
        or case["scores"]["unsupported_assumptions"] == 0
    ]
    passed = (
        not critical_failures
        and structural_percent >= THRESHOLDS["structural_validity_percent"]
        and behavioral_percent >= THRESHOLDS["behavioral_correctness_percent"]
        and semantic_percent >= THRESHOLDS["semantic_quality_percent"]
        and aggregate >= THRESHOLDS["aggregate_percent"]
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "structural_validity_percent": structural_percent,
        "behavioral_correctness_percent": behavioral_percent,
        "semantic_quality_percent": semantic_percent,
        "aggregate_score": aggregate,
        "critical_failures": critical_failures,
    }


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object.")
    return value


def _write_json(path: Path, value: dict[str, Any], *, overwrite: bool = False) -> None:
    mode = "w" if overwrite else "x"
    with path.open(mode, encoding="utf-8", newline="\n") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write("\n")


def _write_jsonl(path: Path, rows: list[dict[str, Any]], *, overwrite: bool = False) -> None:
    mode = "w" if overwrite else "x"
    with path.open(mode, encoding="utf-8", newline="\n") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


class EvaluationRunner:
    def __init__(
        self,
        provider: ReminderProvider | None,
        artifacts_root: str | Path = "artifacts/evaluations",
    ) -> None:
        self.provider = provider
        self.artifacts_root = Path(artifacts_root)

    def _run_directory(self, phase: str, run_id: str) -> Path:
        if phase not in {"initial", "post-repair"}:
            raise ValueError("phase must be 'initial' or 'post-repair'.")
        if Path(run_id).name != run_id or not run_id.startswith(f"{phase}-"):
            raise ValueError("run_id does not match the selected phase.")
        return self.artifacts_root / phase / run_id

    @staticmethod
    def _dataset_hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for block in iter(lambda: file.read(65536), b""):
                digest.update(block)
        return digest.hexdigest()

    def prepare(
        self,
        dataset_path: str | Path,
        *,
        phase: str,
        semantic_method: str,
    ) -> dict[str, Any]:
        if self.provider is None:
            raise ValueError("A configured interpretation provider is required to prepare a run.")
        if semantic_method != "rubric_based":
            raise ValueError("Only rubric_based semantic assessment is configured.")
        dataset = Path(dataset_path).resolve()
        cases = load_dataset(dataset)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{phase}-{timestamp}-{uuid.uuid4().hex[:8]}"
        run_dir = self._run_directory(phase, run_id)
        run_dir.mkdir(parents=True, exist_ok=False)

        results: list[dict[str, Any]] = []
        for case in cases:
            try:
                response = process_request(case["input"], self.provider)
                schema_errors = validate_response(response)
                behavior_errors: list[str] = []
                provider_error = None
            except InvalidProviderOutputError as error:
                response = None
                schema_errors = [str(error)]
                behavior_errors = [str(error)]
                provider_error = str(error)
                behavioral_critical_failure = True
            except UnsafeProviderResponseError as error:
                response = None
                schema_errors = []
                behavior_errors = [str(error)]
                provider_error = str(error)
                behavioral_critical_failure = True
            else:
                behavior_errors, behavioral_critical_failure = (
                    evaluation_behavioral_violations(
                        case["input"],
                        response,
                        case["expected"],
                    )
                )
            structural_pass = not schema_errors
            behavioral_pass = structural_pass and not behavior_errors
            result = {
                "case_id": case["case_id"],
                "input": case["input"],
                "expected": case["expected"],
                "response": response,
                "structural_pass": structural_pass,
                "structural_failures": schema_errors,
                "behavioral_pass": behavioral_pass,
                "behavioral_failures": behavior_errors,
                "critical_failure": not structural_pass or behavioral_critical_failure,
                "scores": None,
                "reasons": None,
                "provider_error": provider_error,
            }
            results.append(result)

        _write_jsonl(run_dir / "cases.jsonl", results)
        _write_jsonl(
            run_dir / "responses.jsonl",
            [
                {"case_id": result["case_id"], "response": result["response"]}
                for result in results
            ],
        )
        _write_jsonl(
            run_dir / "reviewer-packet.jsonl",
            [
                {
                    "case_id": result["case_id"],
                    "expected": result["expected"],
                    "actual_response": result["response"],
                }
                for result in results
            ],
        )
        scores = calculate_scores(results)
        if scores["critical_failures"]:
            scores["status"] = "FAIL"
        report = {
            "run_id": run_id,
            "phase": phase,
            "status": scores["status"],
            "dataset_path": str(dataset),
            "dataset_sha256": self._dataset_hash(dataset),
            "evaluator_method": semantic_method,
            "checks": ["structural", "behavioral", "semantic"],
            "weights": WEIGHTS,
            "thresholds": THRESHOLDS,
            "case_results": results,
            "scores": scores,
        }
        _write_json(run_dir / "report.json", report)
        return report

    def resume(
        self,
        run_id: str,
        dataset_path: str | Path,
        assessments_path: str | Path,
        *,
        phase: str,
        semantic_method: str,
    ) -> dict[str, Any]:
        run_dir = self._run_directory(phase, run_id)
        report_path = run_dir / "report.json"
        report = _read_json(report_path)
        if report.get("run_id") != run_id:
            raise ValueError("The run report does not match the requested run ID.")
        if report.get("evaluator_method") != semantic_method:
            raise ValueError("Semantic method differs from the prepared run.")
        dataset = Path(dataset_path).resolve()
        if report.get("dataset_sha256") != self._dataset_hash(dataset):
            raise ValueError("Dataset identity differs from the prepared run.")

        results = []
        with (run_dir / "cases.jsonl").open(encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Saved case evidence is invalid at line {line_number}."
                    ) from error
        case_ids = [result["case_id"] for result in results]
        try:
            assessments = validate_assessments(
                load_assessments(assessments_path),
                case_ids,
                semantic_method,
            )
        except AssessmentError as error:
            report["status"] = "FAIL"
            report["assessment_errors"] = [str(error)]
            report["scores"] = calculate_scores(results)
            report["scores"]["status"] = "FAIL"
            report["case_results"] = results
            _write_json(report_path, report, overwrite=True)
            return report

        for result in results:
            assessment = assessments[result["case_id"]]
            result["scores"] = assessment["scores"]
            result["reasons"] = assessment["reasons"]
            if assessment["scores"]["unsupported_assumptions"] == 0:
                result["critical_failure"] = True
        scores = calculate_scores(results)
        report["case_results"] = results
        report["scores"] = scores
        report["status"] = scores["status"]
        report.pop("assessment_errors", None)
        _write_json(report_path, report, overwrite=True)
        return report

    def record_human_decision(
        self,
        run_id: str,
        decision: str,
        rationale: str,
        *,
        phase: str = "initial",
    ) -> dict[str, Any]:
        run_dir = self._run_directory(phase, run_id)
        report = _read_json(run_dir / "report.json")
        if report.get("status") not in {"PASS", "FAIL"}:
            raise ValueError("A human decision can only be recorded after final evaluation.")
        normalized_decision = decision.strip().upper()
        if normalized_decision not in {"ACCEPT", "REJECT"}:
            raise ValueError("decision must be ACCEPT or REJECT.")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError("A non-empty human rationale is required.")
        record = {
            "decision": normalized_decision,
            "rationale": rationale.strip(),
            "decision_timestamp": datetime.now(timezone.utc).isoformat(),
            "evaluation_run_id": run_id,
        }
        _write_json(run_dir / "human-decision.json", record)
        return record
