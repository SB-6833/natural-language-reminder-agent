# Quickstart: Natural-Language Reminder Agent — Part 1B

This guide covers the implemented local prototype and its maintained evaluation
dataset.

## Prerequisites

- The existing CPython 3.13.2 virtual environment.
- A genuine live interpretation provider selected by the project owner and
  configured behind the provider-neutral adapter. Do not assume a provider,
  account, API key, or local model is available. Supply any required credentials
  through the operating system's environment/secret mechanism, never embedded in
  commands, source, logs, or reports.
- Semantic assessment is a separate responsibility. Use the specified rubric-based
  method without a second live LLM provider; an LLM judge is optional.
- The project implementation and maintained evaluation corpus in this repository.

## Environment Setup

Activate the existing Python 3.13.2 virtual environment, then verify and install
the project in editable mode:

```powershell
python --version
python -m pip install -e ".[dev]"
```

The editable install provides `jsonschema` and the IANA timezone database at
runtime, plus `pytest` for development. The version check must report Python
3.13.x. Do not put an API key in the shell history or in a repository file.

## Validate Contracts and Unit Behavior

```powershell
python -m pytest
```

Expected result: deterministic schema, format, behavioral checks, and
rubric-assessment tests pass. Tests must use a fake interpretation provider and
must not require network access or credentials.

## Run a Request

Provide one JSON request on standard input using the contract in
[`contracts/reminder-request.schema.json`](./contracts/reminder-request.schema.json):

```powershell
@'
{"request":"Remind me to submit my assignment on 2026-11-20 at 09:00","reference_context":{"current_datetime":"2026-11-12T09:00:00+05:30","timezone":"Asia/Kolkata"}}
'@ | python -m reminder_agent
```

Expected result: standard output contains exactly one response JSON object.
Clarification and rejection outcomes do not require a configured provider. A
complete request requires the owner-selected provider configured through
`REMINDER_AGENT_PROVIDER`; it yields a schema-valid proposed action, and invalid
provider output is not returned as a valid action. Create actions omit
`target_reminder_id`.

For a reschedule or snooze request, provide the `existing_reminders` array with
stable unique IDs. A missing or ambiguous target must yield a clarification and
no action.

## Run, Assess, and Preserve Evaluation

Prepare an initial evaluation run.
This executes the application once per case, saves its outputs and a
case-ID-keyed reviewer packet, and creates a unique run directory:

```powershell
python -m reminder_agent.evaluate --dataset .\data\evaluation_cases.jsonl --phase initial --semantic-method rubric_based --prepare-assessments
```

The evaluation dataset contains one independently validated case per JSON Lines
record. The command reports its unique run ID and preserves the application
outputs and reviewer packet under
`artifacts/evaluations/initial/<run_id>/`. The prepare-only run is
`PENDING_ASSESSMENT`, never a passing evaluation.

Using that packet, the human reviewer supplies one JSON object per case in a
semantic-assessment JSON Lines file. Each object must conform to
[`contracts/semantic-assessment.schema.json`](./contracts/semantic-assessment.schema.json),
include the matching `case_id`, `evaluator_method: "rubric_based"`, all five
0–2 rubric scores, and a non-empty reason for each score. Assess the meaning
against the expected case and saved application response; do not score by exact
string matching alone. A missing, duplicate, unknown, malformed, or invalid
assessment makes final evaluation fail; it must never be treated as passing.

Resume the same run using its reported ID and the reviewer file. The application
is not called again; the evaluator reuses the saved outputs associated with that
run:

```powershell
$runId = "REPLACE_WITH_INITIAL_RUN_ID"
python -m reminder_agent.evaluate --dataset .\data\evaluation_cases.jsonl --phase initial --semantic-method rubric_based --resume-run $runId --semantic-assessments .\data\semantic_assessments.jsonl
```

The finalized report records the dataset path and content hash, evaluator method,
checks, thresholds, per-case results, and supporting evidence. The final human
decision is entered separately from automated PASS/FAIL in
`artifacts/evaluations/initial/<run_id>/human-decision.json`. The reviewer
supplies ACCEPT or REJECT and a non-empty rationale; the record includes the
decision timestamp and associated evaluation run ID. The system never invents
or infers the decision or rationale from the automated result.

After evidence-based repair, preserve the finalized initial report and all its
supporting evidence unchanged. Prepare a new post-repair run with a new run ID,
using the same dataset, checks, semantic method, and thresholds:

```powershell
python -m reminder_agent.evaluate --dataset .\data\evaluation_cases.jsonl --phase post-repair --semantic-method rubric_based --prepare-assessments
```

Use the post-repair run's packet to prepare its own semantic assessment JSONL,
then resume it with the run ID reported by preparation:

```powershell
$postRepairRunId = "REPLACE_WITH_POST_REPAIR_RUN_ID"
python -m reminder_agent.evaluate --dataset .\data\evaluation_cases.jsonl --phase post-repair --semantic-method rubric_based --resume-run $postRepairRunId --semantic-assessments .\data\post_repair_semantic_assessments.jsonl
```

Each phase/run uses a
non-overwriting directory under
`artifacts/evaluations/<phase>/<run_id>/`; the initial evidence remains
unchanged.

The pass thresholds remain aggregate at least 90%, structural validity 100%,
behavioral correctness at least 90%, semantic quality at least 80%, and zero
critical schema or reminder-safety failures. A passing automated result is not
human acceptance; record the explicit decision and rationale separately for the
applicable run.
