"""Command-line entry point for preparing and resuming evaluations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reminder_agent.evaluation import EvaluationRunner
from reminder_agent.interpretation_provider import (
    MissingProviderError,
    ProviderConfigurationError,
    load_provider_from_environment,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate reminder-agent behavior.")
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--phase", required=True, choices=["initial", "post-repair"])
    parser.add_argument(
        "--semantic-method",
        required=True,
        choices=["rubric_based"],
    )
    parser.add_argument("--prepare-assessments", action="store_true")
    parser.add_argument("--resume-run")
    parser.add_argument("--semantic-assessments", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.prepare_assessments == bool(args.resume_run):
        print(
            "Choose exactly one of --prepare-assessments or --resume-run.",
            file=sys.stderr,
        )
        return 2
    if args.resume_run and not args.semantic_assessments:
        print("--semantic-assessments is required with --resume-run.", file=sys.stderr)
        return 2

    try:
        provider = load_provider_from_environment() if args.prepare_assessments else None
        runner = EvaluationRunner(provider)
        if args.prepare_assessments:
            report = runner.prepare(
                args.dataset,
                phase=args.phase,
                semantic_method=args.semantic_method,
            )
        else:
            report = runner.resume(
                args.resume_run,
                args.dataset,
                args.semantic_assessments,
                phase=args.phase,
                semantic_method=args.semantic_method,
            )
    except (
        MissingProviderError,
        ProviderConfigurationError,
        OSError,
        ValueError,
    ) as error:
        print(str(error), file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.resume_run:
        try:
            decision = input("Human decision (ACCEPT/REJECT): ")
            rationale = input("Rationale: ")
            record = runner.record_human_decision(
                args.resume_run,
                decision,
                rationale,
                phase=args.phase,
            )
        except (EOFError, OSError, ValueError) as error:
            print(f"Human decision was not recorded: {error}", file=sys.stderr)
            return 2
        print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
