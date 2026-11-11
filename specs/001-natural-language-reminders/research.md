# Research: Natural-Language Reminder Agent — Part 1B

**Date**: 2026-11-12
**Scope**: Runtime, deterministic validation, test runner, AI-provider boundary,
semantic evaluation, and secret handling.

## Decisions

### Python runtime

- **Decision**: Target CPython 3.13 and use the existing Python 3.13.2 virtual
  environment.
- **Rationale**: This preserves compatibility with the user's available
  environment. The official Python version-status table lists 3.13 in security
  support through October 2029.
- **Alternatives considered**: Python 3.14 is not the target because the project
  already has a compatible Python 3.13.2 environment.
- **Source**: [Python Developer's Guide: Status of Python versions](https://devguide.python.org/versions/)

### Deterministic response validation

- **Decision**: Keep JSON Schema as the response contract and validate it with
  `jsonschema` using Draft 2020-12 and an explicitly enabled format checker.
- **Rationale**: This keeps the documented contract independent of the model and
  makes required fields, conditional action shapes, and extra-field rejection
  auditable. The library documents that `format` checks are not automatically
  enforced unless a format checker is supplied. Time-zone identifiers and
  cross-record ID uniqueness need deterministic checks beyond standard JSON
  Schema.
- **Alternatives considered**: Pydantic provides strict validation and JSON Schema
  generation, but using it as a second contract model risks divergence from the
  assignment's independently validated JSON Schema.
- **Sources**: [`jsonschema` validation](https://python-jsonschema.readthedocs.io/en/stable/validate/);
  [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/);
  [Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/).

### Test runner

- **Decision**: Use `pytest` as the sole test runner.
- **Rationale**: Parametrized tests fit the specification's category-based case
  coverage and make case-level failures easy to inspect.
- **Alternatives considered**: The standard-library `unittest` avoids a test
  dependency but offers less concise parametrized coverage. Do not use both.
- **Sources**: [pytest parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html);
  [Python `unittest`](https://docs.python.org/3/library/unittest.html).

### Live interpretation provider and semantic evaluator

- **Decision**: Keep live reminder interpretation behind the provider-neutral
  adapter accepted during planning. Keep semantic assessment as a separate
  responsibility that applies the spec's five-dimension rubric and records the
  evaluator method used. Rubric-based assessment is supported without a second
  live LLM provider; an LLM judge is optional.
- **Rationale**: No provider, data-sharing policy, account, or API key was specified.
  A neutral interpretation boundary avoids an unapproved vendor/privacy decision
  while retaining the required AI behavior when an adapter is configured.
  Separating the evaluator avoids coupling scoring to the live interpretation
  provider and permits rubric assessment without another live model.
- **Alternatives considered**: A hosted provider offers structured-output
  features but sends request content externally and requires provider-specific
  credentials. A local model avoids hosted data transfer but adds runtime and
  resource requirements not specified by the assignment. Requiring a second live
  LLM for semantic scoring would add a provider dependency not required by the
  spec.
- **Constraint**: All semantic methods must produce the five rubric scores and
  reasons and record the evaluator method. If an LLM judge is selected, its output
  is validated against its own schema; a constrained judge response does not prove
  the assessment is correct. Structural and behavioral checks remain deterministic,
  independent, and authoritative.
- **Source**: [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs/)
  is an example of a vendor-specific constrained-output feature, not a selected
  dependency.

### Evaluation evidence and secret handling

- **Decision**: Keep the evaluation harness local and create a unique,
  non-overwriting `artifacts/evaluations/<phase>/<run_id>/` directory for each
  run. Use `initial` and `post-repair` phases. Record the dataset identity (path
  and content hash), evaluator method, checks, thresholds, per-case outputs and
  results, and supporting evidence. Preserve the finalized initial report and all
  supporting evidence unchanged during repair and post-repair evaluation.
- **Human decision**: Store the human-entered ACCEPT/REJECT decision and
  non-empty rationale separately from automated PASS/FAIL. Include the decision
  timestamp and associated unique evaluation run ID in the record. Never infer
  the decision or rationale from automated results.
- **Rationale**: Unique run directories prevent accidental replacement of
  evidence and support auditably identical post-repair checks. Credentials remain
  runtime configuration, never source, output, logs, or evidence.
- **Sources**: [OpenAI API key safety guidance](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety);
  [OpenAI Evals guide](https://developers.openai.com/api/docs/guides/evals) notes
  the platform's scheduled retirement in November 2026, further supporting a
  local, provider-neutral harness.

## Planning Implications

- The application response schema, evaluation-case schema, and semantic-assessment
  schema are separate artifacts.
- Each JSON Lines record is one case and is parsed and schema-validated
  independently; malformed records are reported, never silently skipped.
- JSON Schema validation handles response shape and formats; deterministic
  behavioral checks handle properties such as unique reminder IDs and no invented
  schedule/target details.
- Semantic evaluation records one 0-2 score and reason for each rubric dimension
  and the method used. The live interpretation provider and semantic evaluator
  remain separate; a second live LLM is optional, not mandatory.
- Rubric-based human assessments are supplied as JSON Lines, one semantic
  assessment per evaluation case. Each assessment is validated against the
  semantic-assessment schema and joined by `case_id`; duplicate, unknown, missing,
  malformed, or invalid assessments fail final evaluation and cannot count as a
  passing semantic score. A prepare-only run remains pending, never passing.
- The evaluation CLI is provided by `src/reminder_agent/evaluate.py`; it prepares
  a reviewer packet from saved application outputs and resumes the same run using
  reviewer assessments without rerunning the interpretation provider.
- A final human decision record is distinct from automated PASS/FAIL and carries
  the reviewer decision, rationale, timestamp, and associated run ID.
- No evaluation cases or application code are created in this planning phase.
