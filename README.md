# Natural Language Reminder Agent

## Overview
A spec-driven natural-language reminder agent developed as part of the BITS WILP AI-Augmented SDLC assignment.

The application interprets reminder requests and produces structured JSON responses for creating reminders, rescheduling or snoozing existing reminders, and asking clarification questions when required information is missing.

## Key Features
- Natural-language reminder request handling through a provider adapter.
- Structured JSON response contract.
- Clarification when mandatory information is missing.
- Safe handling of reschedule and snooze requests using supplied reminder records.
- Independent schema, behavioral, and semantic evaluation design.
- Evaluation dataset containing 21 cases across six categories.
- Automated unit and integration tests.

## Technology Stack
- Python 3.13
- JSON and JSON Schema
- Pytest
- Git and GitHub
- GitHub Spec Kit for Spec-Driven Development

## Project Structure
- `.specify/` – Spec Kit configuration and memory
- `.github/skills/` – Spec Kit workflow skills
- `specs/` – Requirements, plan, tasks, and contracts
- `src/reminder_agent/` – Application implementation
- `data/` – Evaluation dataset
- `tests/` – Unit and integration tests

## Setup

Create and activate a Python 3.13 virtual environment, then install the project dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Run the automated tests:

```powershell
python -m pytest -q
```

Run the application:

```powershell
python -m reminder_agent
```

## Evaluation Status
- 21 evaluation cases prepared and dataset structure validated.
- 27 automated tests passed in the local development environment.
- Static security scan and Python compilation checks passed.
- Live interpretation-provider configuration and provider-dependent end-to-end evaluation remain pending.

The application intentionally fails closed when no approved interpretation provider is configured. No provider credentials or secrets are committed to this repository.

## Development Approach
The project follows a Spec-Driven Development workflow: Constitution → Specify → Clarify → Plan → Tasks → Analyze → Implement → Validate.

Automated validation is kept separate from the final human review and acceptance decision.