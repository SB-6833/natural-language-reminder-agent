# Implementation Plan: Natural-Language Reminder Agent — Part 1B

**Branch**: `001-natural-language-reminders` | **Date**: 2026-11-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-natural-language-reminders/spec.md`

## Summary

Build a local Python package with a JSON-in/JSON-out reminder interface. Keep
natural-language interpretation behind a vendor-neutral AI provider adapter;
validate every response against the strict response schema before returning it.
Keep the live reminder-interpretation provider separate from the semantic
evaluator. The semantic evaluator applies the specification's five-dimension
rubric and records the method used; rubric-based assessment is supported without
requiring a second live LLM provider. A single evaluation runner will score the
maintained cases, preserve the initial report and supporting evidence, and
require an explicit human decision after automated results. Each decision records
ACCEPT or REJECT, a non-empty reviewer-entered rationale, its timestamp, and the
unique evaluation run ID, separately from automated PASS/FAIL. The prototype has
no reminder store and performs no notification or external scheduling operation.

## Technical Context

**Language/Version**: CPython 3.13; compatible with the existing Python 3.13.2
virtual environment.

**Primary Dependencies**: `jsonschema` with Draft 2020-12 and explicit format
checking; `pytest` for tests. The live interpretation provider is injected
through a vendor-neutral adapter; no provider SDK is selected in this plan.
Semantic assessment is a separate rubric-based responsibility; an LLM judge is
optional and does not require a second live provider.

**Storage**: No reminder persistence. Evaluation cases are planned as JSON Lines;
each line is one independently parsed and validated case. Evaluation evidence is
saved in local, non-overwriting
`artifacts/evaluations/<phase>/<run_id>/` directories, where phase is `initial`
or `post-repair` and every run ID is unique. The finalized initial report and its
supporting evidence are preserved unchanged during repair and post-repair
evaluation. Each run records the dataset path and content hash, evaluator
method, checks, thresholds, and per-case results.

**Testing**: `pytest`, with deterministic unit tests for schema and behavioral
checks and integration tests using a fake interpretation provider and
rubric-based semantic assessment. Reviewer assessments are supplied as
case-keyed JSON Lines validated against the semantic-assessment contract; missing
or invalid assessments cannot produce a passing evaluation. Tests do not require
live AI credentials.

**Target Platform**: Local, cross-platform Python environment; validate on Windows
and keep paths and commands portable where practical.

**Project Type**: Small importable Python package with a JSON stdin/stdout CLI;
the evaluator calls the same application entry point.

**Performance Goals**: No production latency or throughput target is specified.
The prototype is sized for a local evaluation corpus of at least 20 cases.

**Constraints**: No external scheduling, notifications, or reminder database.
Interpretation-provider credentials, if required by a configured adapter, are
read at runtime from the environment and are never written to source, logs, or
evidence. Semantic scoring follows the five-dimension rubric in the spec and
records the evaluator method. Structural validation, critical behavioral checks,
and semantic judgment remain separate gates. The human decision record contains
the reviewer-entered ACCEPT/REJECT decision, non-empty rationale, decision
timestamp, and unique evaluation run ID, separate from automated PASS/FAIL; the
system never invents or infers the human decision or rationale.

**Scale/Scope**: One assignment prototype and one local evaluation workflow. The
evaluation corpus must cover all 20 cases enumerated in the specification; it is
not created by this planning command.

## Constitution Check

**Pre-design gate: PASS**

- **I. Requirements Before Implementation**: The approved specification defines
  user scenarios, testable functional requirements, and measurable outcomes.
- **II. Plans Must Trace to Requirements**: Each design artifact maps to the
  specification; the existing `tasks.md` maps implementation work to approved
  requirements.
- **III. Changes Must Be Verifiable**: The plan includes focused automated tests
  and a complete evaluation run.
- **IV. Keep Changes Small and Consistent**: The proposed package is limited to
  application, provider boundary, validation, evaluation, and CLI concerns.
- **V. Protect User Data and Secrets**: No secrets are committed or persisted in
  output/evidence; provider credentials are runtime-only.
- **VI. Structured AI Outputs**: Strict JSON Schemas define request and response
  contracts; invalid model outputs cannot become valid actions.
- **VII. Reminder Safety**: Missing or ambiguous fields and targets lead to
  clarification; adversarial input cannot bypass validation.
- **VIII. Independent Evaluation**: The design supports the required 20-case
  coverage set and a maintained dataset.
- **IX. Layered Validation**: Structural checks, behavioral invariants, and
  semantic scoring are distinct evaluation stages.
- **X. Predeclared Quality Threshold**: The 40/40/20 weights, component
  thresholds, and critical-failure gates are fixed before final evaluation.
- **XI. Evidence-Based Repair**: Initial evidence is preserved; repairs rerun the
  same cases, evaluator configuration, checks, and thresholds.
- **XII. Human Oversight**: Automated results require a recorded human
  ACCEPT/REJECT decision, rationale, timestamp, and evaluation run ID, separate
  from automated PASS/FAIL.

No constitution violations or exceptions are required.

## Project Structure

### Documentation (this feature)

```text
specs/001-natural-language-reminders/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── reminder-request.schema.json
│   ├── reminder-response.schema.json
│   ├── evaluation-case.schema.json
│   └── semantic-assessment.schema.json
└── tasks.md             # Existing implementation task list
```

### Source Code (repository root)

```text
pyproject.toml
src/
└── reminder_agent/
    ├── __init__.py
    ├── __main__.py
    ├── application.py
    ├── interpretation_provider.py
    ├── validation.py
    ├── semantic_assessment.py
    ├── evaluation.py
    └── evaluate.py
tests/
├── unit/
└── integration/
data/
└── evaluation_cases.jsonl
artifacts/
└── evaluations/
    ├── initial/
    │   └── <run_id>/
    └── post-repair/
        └── <run_id>/
```

**Structure Decision**: Use one importable package. `application.py` coordinates
request interpretation and safe response handling; `interpretation_provider.py`
defines the injectable live AI provider boundary; `validation.py` owns
deterministic schema and behavior checks; `semantic_assessment.py` applies the
five-dimension rubric and records the evaluator method; `evaluation.py` validates
each JSON Lines case independently, orchestrates the stages, and records
scores/evidence; `evaluate.py` provides the evaluation CLI. `__main__.py` provides
the JSON stdin/stdout application entry point. Each evaluation creates a unique
run directory without overwriting existing evidence. The data and evidence
locations above are planned locations; this command creates design artifacts
only, not source code or evaluation cases.

**Provider Decision**: Use a provider-neutral adapter, with no vendor selected or
SDK included for live reminder interpretation. The semantic evaluator is a
separate responsibility: rubric-based assessment is supported by default, while
an LLM judge is optional. No second live LLM provider is required. Each evaluation
report records the semantic evaluator method used. Tests use deterministic fakes
for live interpretation. A genuine provider must be selected and configured by
the project owner before the final live demonstration; no provider, account, API
key, or local model is assumed to be available. Credentials are runtime-only. A
missing interpretation-provider configuration must be reported explicitly and
must not produce a success-shaped fallback.

**Post-design gate: PASS**. The design keeps application, structural validation,
behavioral validation, semantic scoring, evidence preservation, and human
acceptance distinct and does not add a reminder store or scheduling integration.

## Complexity Tracking

No constitution violations; no complexity exception is needed.
