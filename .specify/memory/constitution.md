<!--
Sync Impact Report
Version change: 1.0.0 -> 1.1.0
Modified principles: None; all existing principles and governance are retained.
Added principles: VI. Structured AI Outputs; VII. Reminder Safety; VIII. Independent Evaluation; IX. Layered Validation; X. Predeclared Quality Threshold; XI. Evidence-Based Repair; XII. Human Oversight.
Added sections: None.
Removed sections: None.
Follow-up TODO: None; the project owner approved ratification on 2026-11-12.
-->

# Reminder Agent Constitution

## Core Principles

### I. Requirements Before Implementation
Every feature MUST have a written specification with observable acceptance criteria
before implementation begins. Ambiguities that affect behavior MUST be resolved or
recorded as explicit assumptions. This keeps implementation tied to user outcomes.

### II. Plans Must Trace to Requirements
Implementation plans and task lists MUST map work to the approved specification.
Changes outside that scope require an explicit specification update. This prevents
unreviewed scope expansion.

### III. Changes Must Be Verifiable
Behavior changes MUST include focused tests or a documented reason why automated
testing is not applicable. Contributors MUST run the smallest relevant existing
validation command and report its outcome. This makes regressions observable.

### IV. Keep Changes Small and Consistent
Changes MUST address the requested behavior without unrelated edits and MUST follow
established project patterns. Shared behavior MUST reuse existing helpers where
appropriate. This reduces maintenance cost and unintended impact.

### V. Protect User Data and Secrets
Credentials and secrets MUST NOT be committed. Features that handle user data MUST
collect and retain only what their documented behavior requires. This reduces
avoidable privacy and security risks.

### VI. Structured AI Outputs
All AI-generated reminder responses MUST conform to a documented output schema.
Invalid or incomplete outputs MUST be rejected or handled safely; they MUST NOT be
treated as valid reminder data.

### VII. Reminder Safety
The agent MUST NOT invent missing dates, times, time zones, or reminder details. It
MUST ask for clarification when mandatory information is missing or ambiguous.
Malformed and adversarial inputs MUST be handled safely and MUST NOT bypass these
requirements.

### VIII. Independent Evaluation
The project MUST maintain an evaluation dataset containing at least 15 meaningful
cases. Collectively, the cases MUST cover normal, boundary, ambiguous,
missing-information, malformed, and adversarial inputs.

### IX. Layered Validation
The evaluation harness MUST independently perform structural schema validation,
behavioral invariant or property checks, and semantic or quality evaluation. An
LLM judge MUST NOT replace deterministic structural and behavioral checks.

### X. Predeclared Quality Threshold
Evaluation criteria, scoring method, and pass threshold MUST be documented before
final evaluation. A passing aggregate score MUST NOT override any critical safety
or structural failure.

### XI. Evidence-Based Repair
Initial evaluation results MUST be preserved. Repairs MUST be based on actual
failure evidence, and the same evaluation checks MUST be rerun after repair. Tests,
acceptance criteria, and evaluation thresholds MUST NOT be weakened merely to
obtain a pass.

### XII. Human Oversight
Final evaluation results MUST be presented for an explicit human ACCEPT/REJECT
decision. A PASS result alone MUST NOT imply human acceptance.

## Additional Constraints

Project-specific technology, performance, and deployment requirements MUST be
documented in the applicable feature specification or plan when established. No
stack-specific constraints are defined by the current repository materials.

## Development Workflow

Feature work MUST proceed from specification to clarification as needed, then to
planning, task breakdown, implementation, and validation. Reviews MUST check that
the delivered behavior meets the acceptance criteria and that relevant tests pass.
Documentation directly affected by a change MUST be updated.

## Governance

This constitution governs project decisions and supersedes conflicting local
conventions. Amendments MUST be made in this file, reviewed with the affected
specifications and practices, and accompanied by a semantic version increment.
MAJOR increments mark backward-incompatible governance changes; MINOR increments
mark new or materially expanded principles; PATCH increments mark clarifications
and non-semantic refinements.

Contributors and reviewers MUST check proposed work against these principles.
Exceptions MUST be documented with their rationale in the relevant specification
or review record. Any affected guidance or workflow MUST be updated when an
amendment changes it.

**Version**: 1.1.0 | **Ratified**: 2026-11-12 | **Last Amended**: 2026-11-12
