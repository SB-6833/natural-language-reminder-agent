# Tasks: Natural-Language Reminder Agent — Part 1B

**Input**: Design documents from `specs/001-natural-language-reminders/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`

**Tests**: Focused unit and integration tests are included as required by the plan and project constitution.

**Organization**: Tasks are grouped by the four P1 user stories. Stories are sequenced because they extend the shared application dispatcher, and the evaluation story depends on the completed reminder behaviors.

## Phase 1: Setup

**Purpose**: Establish the Python package and its supported runtime.

- [X] T001 Initialize `pyproject.toml` as a `src/`-layout package targeting CPython `>=3.13,<3.14`, with `jsonschema` and `tzdata` as runtime dependencies and `pytest` as a development dependency.

---

## Phase 2: Foundational

**Purpose**: Implement shared package, provider, schema-validation, application, and CLI boundaries required by every story.

- [X] T002 [P] Create the package marker and public package metadata in `src/reminder_agent/__init__.py`.
- [X] T003 [P] Define the injectable, vendor-neutral interpretation-provider interface and explicit missing-provider error behavior in `src/reminder_agent/interpretation_provider.py`; do not select a vendor SDK or add credentials, and retain deterministic fakes for automated tests.
- [X] T004 [P] Load the request, response, evaluation-case, and semantic-assessment contracts and validate JSON using Draft 2020-12 with explicit format checking in `src/reminder_agent/validation.py`.
- [X] T005 Create the shared request-dispatch and provider-injection entry point in `src/reminder_agent/application.py`, returning only JSON-compatible proposed outcomes.
- [X] T006 Add the JSON stdin/stdout application entry point in `src/reminder_agent/__main__.py`; serialize one response object and report provider or validation errors explicitly.

**Checkpoint**: Package setup, provider boundary, schema validation, application entry point, and CLI are available before story implementation.

---

## Phase 3: User Story 1 — Create a Reminder (Priority: P1)

**Goal**: Turn a sufficiently clear creation request into a schema-valid proposed create action without inventing details or performing external scheduling.

**Independent Test**: Provide a clear creation request and explicit reference context to an injected provider; verify the action's task and resolved schedule, confirm it omits `target_reminder_id`, and verify no notification or scheduling side effect occurs.

### Tests for User Story 1

- [X] T007 [P] [US1] Add unit tests for create-response contract rules, including required `task`, `date`, `time`, and `timezone` fields and prohibited `target_reminder_id`, in `tests/unit/test_create_reminder.py`.
- [X] T008 [P] [US1] Add integration tests for explicit and relative-date create requests, missing schedule information, unknown time zone, and proposal-only behavior in `tests/integration/test_create_reminder.py`.

### Implementation for User Story 1

- [X] T009 [US1] Implement provider-backed create interpretation in `src/reminder_agent/application.py`; require a clear task, date, and time, resolve relative dates only from supplied reference context, preserve an unspecified time zone as `null`, validate the response, and never send notifications or schedule externally.

**Checkpoint**: User Story 1 can be exercised independently through the JSON interface using an injected provider.

---

## Phase 4: User Story 2 — Reschedule or Snooze a Reminder (Priority: P1)

**Goal**: Produce reschedule or snooze proposals only for a uniquely matched caller-supplied reminder and a sufficiently clear destination schedule.

**Independent Test**: Supply a uniquely identified reminder record and a clear reschedule or snooze request; verify the action kind, exact target ID, task, and resulting schedule. Also verify missing, unmatched, duplicate, or ambiguous targets produce no action.

### Tests for User Story 2

- [X] T010 [P] [US2] Add unit tests for existing-reminder field validation, unique IDs, exact target-ID copying, and update-response requirements in `tests/unit/test_update_reminders.py`.
- [X] T011 [P] [US2] Add integration tests for uniquely matched reschedule and snooze requests, unchanged schedule components, and missing or ambiguous target clarification in `tests/integration/test_update_reminders.py`.

### Implementation for User Story 2

- [X] T012 [US2] Validate caller-supplied context in `src/reminder_agent/validation.py`: `reminder_id` is non-empty and unique within the supplied list; `task` is non-empty; `date` is `YYYY-MM-DD`; `time` is 24-hour `HH:MM`; `timezone` is an IANA identifier when known, otherwise null; `reference_context.current_datetime` is ISO-8601 with UTC offset and `reference_context.timezone` is an IANA time-zone identifier or `null`.
- [X] T013 [US2] Implement reschedule and snooze target matching in `src/reminder_agent/application.py`; require an identifying request reference that matches exactly one supplied record, copy that record's exact ID and task, clarify on missing or non-unique targets, and copy an unchanged schedule component only when the request clearly leaves it unchanged.

**Checkpoint**: User Stories 1 and 2 work independently for their respective action types and never invent or select a target ID.

---

## Phase 5: User Story 3 — Clarify or Reject Unsafe Requests (Priority: P1)

**Goal**: Safely clarify missing, ambiguous, or contradictory required information and reject or safely reformulate malformed, irrelevant, or adversarial input without emitting an unsafe action.

**Independent Test**: Submit representative missing, contradictory, malformed, irrelevant, and adversarial requests; verify focused clarification or safe rejection and no reminder action whenever required information is unresolved.

### Tests for User Story 3

- [X] T014 [P] [US3] Add unit tests for focused clarification and rejection response shapes, including missing task/date/time, contradictory details, and unresolved update targets, in `tests/unit/test_safe_outcomes.py`.
- [X] T015 [P] [US3] Add integration tests for malformed, irrelevant, and adversarial inputs, including attempts to override safety or response-format rules, in `tests/integration/test_safe_outcomes.py`.

### Implementation for User Story 3

- [X] T016 [US3] Implement deterministic behavioral checks in `src/reminder_agent/validation.py` for unresolved mandatory information, action/intent consistency, exact unique update targets, unsupported details, and unsafe-input attempts; fail closed rather than treating an invalid response as an action.
- [X] T017 [US3] Implement focused clarification and safe rejection handling in `src/reminder_agent/application.py`; return no action payload for either outcome and never infer a date, time, time zone, task, target, or action from missing or ambiguous input.

**Checkpoint**: All reminder actions are withheld whenever the request is incomplete, ambiguous, contradictory, malformed, irrelevant, or adversarial in a way that prevents safe interpretation.

---

## Phase 6: User Story 4 — Evaluate Reminder Behavior (Priority: P1)

**Goal**: Run all maintained cases through one layered evaluation pipeline, preserve evidence, apply predeclared scoring gates, and present results for a human decision.

**Independent Test**: Run the complete dataset and verify per-case structural, behavioral, and semantic results; check the 40/40/20 score and thresholds; confirm initial evidence remains intact after a post-repair run; and verify final results request explicit ACCEPT or REJECT.

### Tests for User Story 4

- [X] T018 [P] [US4] Add unit tests for independent JSONL-line parsing, case-schema failures, semantic assessment score/reason validation and case-ID matching, missing or invalid assessment failure, weighted score calculation, and critical-failure gates in `tests/unit/test_evaluation.py`.
- [X] T019 [P] [US4] Add integration tests proving one pipeline evaluates the dataset through the application and all three check layers, preserves initial report and supporting evidence unchanged in unique run directories, rejects missing/invalid rubric assessments, and fails when the unsupported-assumptions score is 0 even if the aggregate score is high; validate that the separate human decision record contains ACCEPT or REJECT, a non-empty reviewer-entered rationale, a decision timestamp, and the evaluation run ID matching the corresponding evaluation, independently of automated PASS/FAIL, in `tests/integration/test_evaluation_pipeline.py`.

### Implementation for User Story 4

- [X] T020 [P] [US4] Create `data/evaluation_cases.jsonl` with at least 20 meaningful cases, one independently valid JSON object per line, covering all six categories and every distinct case in FR-011; use `case_id` values matching `^C[0-9]{2,}$` and category values `normal`, `boundary`, `ambiguous`, `missing_information`, `malformed`, or `adversarial`.
- [X] T021 [US4] Implement the JSON Lines case loader in `src/reminder_agent/evaluation.py`; parse and validate each line independently against `specs/001-natural-language-reminders/contracts/evaluation-case.schema.json`, and report invalid line numbers and case IDs when available without silently skipping a case.
- [X] T022 [US4] Implement deterministic per-case structural and behavioral evaluation in `src/reminder_agent/validation.py`, including response shape, action-specific fields, input-to-action invariants, target identity, unsupported assumptions, and critical safety failures.
- [X] T023 [US4] Implement rubric-based human assessment intake in `src/reminder_agent/semantic_assessment.py`; accept reviewer-supplied JSON Lines with exactly one `SemanticAssessment` per case, conforming to `specs/001-natural-language-reminders/contracts/semantic-assessment.schema.json` with the matching `case_id`, `evaluator_method: "rubric_based"`, all five 0–2 scores, and a non-empty reason for each dimension; provide expected meaning and actual response as reviewer context, allow meaning-equivalent wording rather than exact-string-only matching, and do not require a second live LLM.
- [X] T024 [US4] Implement the single evaluation runner in `src/reminder_agent/evaluation.py` to invoke the application for every case, validate and join exactly one semantic assessment to each dataset `case_id`, reject duplicate, unknown, missing, malformed, or schema-invalid assessments as final evaluation failures that cannot pass, classify any unsupported-assumptions dimension score of 0 as a critical safety failure, keep a prepare-only run `PENDING_ASSESSMENT` rather than `PASS`, and collect separate structural, behavioral, and semantic results, per-case failures, and critical-failure flags.
- [X] T025 [US4] Calculate evaluation scores in `src/reminder_agent/evaluation.py`; calculate `Semantic score (%) = (total points earned / total possible points) × 100` across the five 0–2 scoring dimensions, and weight structural validity at 40%, behavioral correctness at 40%, and semantic quality at 20%; pass only at aggregate `>=90%`, structural validity `100%`, behavioral correctness `>=90%`, semantic quality `>=80%`, and zero critical schema or reminder-safety failures, including any unsupported-assumptions dimension score of 0 regardless of aggregate score.
- [X] T026 [US4] Preserve initial and post-repair reports plus supporting evidence in non-overwriting `artifacts/evaluations/<phase>/<run_id>/` directories, assigning a unique run ID to each evaluation and refusing to overwrite an existing directory; preserve the finalized initial report and all its supporting evidence unchanged during repair and post-repair evaluation; record dataset identity (path and content hash), evaluator method, checks, thresholds, and per-case results for both runs in `src/reminder_agent/evaluation.py`.
- [X] T027 [US4] After automated evaluation completes, collect an explicit human `ACCEPT` or `REJECT` and non-empty reviewer-entered rationale in `artifacts/evaluations/<phase>/<run_id>/human-decision.json`; record the decision timestamp and the evaluation run ID matching the corresponding evaluation in that record, keep it separate from automated `PASS`/`FAIL`, and never infer acceptance from a `PASS`, in `src/reminder_agent/evaluation.py`.
- [X] T028 [US4] Add the evaluation command entry point in `src/reminder_agent/evaluate.py` with dataset, initial/post-repair phase, semantic-method, `--prepare-assessments`, `--resume-run <run_id>`, and `--semantic-assessments <path>` options; preparation must create a unique run directory and case-ID-keyed reviewer packet from the actual application outputs, while resume must reuse those preserved outputs without rerunning the provider, require exactly one valid assessment per case, and retain the same dataset, checks, method, and thresholds for repair reruns.

**Checkpoint**: The complete evaluation pipeline covers the maintained dataset, preserves initial evidence, enforces every independent gate, and records the explicit human decision.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Align the run guide with the delivered workflow, review secret handling, and validate the complete feature.

- [ ] T029 Obtain the project owner's explicit choice of at least one genuine AI interpretation provider for the final demonstration, confirm account/model/access prerequisites, and configure its adapter behind the vendor-neutral interface in `src/reminder_agent/interpretation_provider.py`; keep credentials runtime-only and never write them to source, logs, outputs, or evidence, do not assume a provider, API key, or local model is available, and retain deterministic fakes for automated tests.
- [X] T030 [P] Update `specs/001-natural-language-reminders/quickstart.md` with the implemented Python 3.13 setup, owner-confirmed live-provider prerequisites, runtime-only credential configuration, application and evaluation commands, rubric-based semantic-assessment file workflow, evidence locations, thresholds, and separate human decision record.
- [ ] T031 Run `pytest` and the end-to-end scenarios documented in `specs/001-natural-language-reminders/quickstart.md` using the configured genuine provider for the final demonstration; keep automated tests on deterministic fakes, and fix only failures supported by test or evaluation evidence without weakening criteria or thresholds.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 initializes the package and dependencies.
- **Foundational (Phase 2)**: T002–T006 depend on T001 and block all user stories.
- **User Story 1 (Phase 3)**: Depends on the foundation; it is the MVP increment.
- **User Story 2 (Phase 4)**: Follows User Story 1 because both extend the shared application dispatcher and response validation.
- **User Story 3 (Phase 5)**: Follows User Story 2 because its safety outcomes must cover both create and update flows.
- **User Story 4 (Phase 6)**: Depends on all reminder behaviors so every evaluation case exercises the implemented application; final live demonstration depends on completing T029.
- **Polish (Phase 7)**: Depends on the desired stories, with final validation after implementation.

### User Story Dependencies

- **US1 (P1)**: Starts after foundational tasks; no dependency on another story.
- **US2 (P1)**: Starts after US1; extends the common application and request-context validation.
- **US3 (P1)**: Starts after US2; applies clarification and rejection behavior across create and update actions.
- **US4 (P1)**: Starts after US1–US3; evaluates their complete behavior and preserves initial/post-repair evidence.

### Parallel Opportunities

- T002, T003, and T004 work on separate files and can proceed in parallel after T001.
- Within each story, the separate unit and integration test files can be prepared in parallel.
- T020 dataset authoring can proceed alongside the US4 test-file preparation.
- T029 provider configuration and T030 quickstart updates touch separate files and can proceed in parallel when the owner has confirmed the provider.
- User-story implementation phases are intentionally sequential because they modify shared application and validation modules.

## Parallel Example: User Story 1

```text
Task: "Add unit tests for create-response contract rules in tests/unit/test_create_reminder.py"
Task: "Add integration tests for create requests in tests/integration/test_create_reminder.py"
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Complete User Story 1 and validate create actions independently.
3. Keep the MVP limited to proposed create actions; do not add notification or external scheduling behavior.
4. Complete User Stories 2 and 3 before evaluating the full assignment.

### Incremental Delivery

1. Establish package, provider, and schema-validation foundations.
2. Deliver US1 create proposals.
3. Deliver US2 reschedule and snooze proposals using uniquely matched caller-supplied records.
4. Deliver US3 clarification and rejection safeguards across all reminder actions.
5. Deliver US4 dataset evaluation, preserved evidence, scoring gates, and human decision.
6. Run the quickstart and full test suite without weakening cases or acceptance thresholds.

## Notes

- Every task uses the required checkbox, sequential ID, optional parallel marker, required user-story label, and concrete file path.
- `[P]` marks only independent work in different files; tasks that share the application or validation modules remain sequential.
- Tests are included because the plan and constitution require verifiable behavior.
- No application code, tests, or evaluation cases are created by this task-list document.
