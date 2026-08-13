"""Run an eval you can type, not one you paste.

The harness's only interface used to be Python: suites were module
constants, improvements were factory functions, and running anything meant
writing a `python -c` incantation. This module is the thin, discoverable
translation of what `harness/runner.py` already does -- suites and
improvements addressed by name, `--help` as the documentation, and
failures that say what to fix.

    uv run python -m harness.cli --help
    uv run python -m harness.cli suites
    uv run python -m harness.cli one --suite duration
    uv run python -m harness.cli batch --suite duration \\
        --improvement tech-stack-only

Comparison stays deliberately manual: `summarize` reads a checkpoint and
compares nothing. The engine (`run_suite`/`run_batch`) is untouched; this
translates it.
"""

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from harness.pi_invocation import DEFAULT_MODEL
from harness.runner import (
    IMPROVEMENTS,
    SUITES,
    Improvement,
    RunResult,
    run_batch,
    run_suite,
)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_REFUSED = 2


def _resolve_improvement(name: str | None) -> Improvement | None:
    """The named improvement's factory result, or None for a bare run."""
    if name is None:
        return None
    return IMPROVEMENTS[name]()


def _rejection_reasons(result: RunResult) -> list[str]:
    """The grade signals that explain why a run was not accepted."""
    grade = result.grade
    reasons = []
    if grade.refused_config:
        reasons.append(f"refused_config={','.join(grade.refused_config)}")
    if grade.timed_out or result.pi_timed_out:
        reasons.append("timed_out")
    if grade.returncode not in (0, None):
        if grade.tests_executed < grade.tests_expected:
            reasons.append(
                f"returncode={grade.returncode} "
                f"({grade.tests_executed}/{grade.tests_expected} tests passed)"
            )
        else:
            reasons.append(f"returncode={grade.returncode}")
    elif grade.tests_executed < grade.tests_expected:
        reasons.append(f"tests_executed {grade.tests_executed}/{grade.tests_expected}")
    return reasons


def _cmd_suites(args: argparse.Namespace) -> int:
    for key in sorted(SUITES):
        print(f"{key} ({SUITES[key].name})")
    return EXIT_OK


def _cmd_improvements(args: argparse.Namespace) -> int:
    for key in sorted(IMPROVEMENTS):
        print(key)
    return EXIT_OK


def _cmd_one(args: argparse.Namespace) -> int:
    result = run_suite(
        SUITES[args.suite],
        model=args.model,
        timeout=args.timeout,
        improvement=_resolve_improvement(args.improvement),
    )
    if result.accepted:
        grade = result.grade
        print(f"accepted: {grade.tests_executed}/{grade.tests_expected} tests passed")
    else:
        print("rejected: " + ", ".join(_rejection_reasons(result)))
    return EXIT_OK


def _cmd_batch(args: argparse.Namespace) -> int:
    if args.target < 0:
        print("refused: --target must not be negative", file=sys.stderr)
        return EXIT_REFUSED
    checkpoint = args.checkpoint
    if checkpoint is None:
        checkpoint = (
            Path.home() / "evidence" / f"{args.suite}-{date.today().isoformat()}.jsonl"
        )
    results = run_batch(
        checkpoint,
        suite=SUITES[args.suite],
        target=args.target,
        model=args.model,
        improvement=_resolve_improvement(args.improvement),
        timeout=args.timeout,
    )
    for index, result in enumerate(results, start=1):
        if result.accepted:
            print(f"run {index}: accepted")
        else:
            reasons = _rejection_reasons(result)
            print(f"run {index}: rejected ({', '.join(reasons)})")
    accepted = sum(1 for result in results if result.accepted)
    print(f"batch complete: {accepted}/{len(results)} accepted")
    print(f"wrote {len(results)} runs to {checkpoint}")
    return EXIT_OK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness.cli", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    suites = subparsers.add_parser("suites", help="list the suites by name")
    suites.set_defaults(func=_cmd_suites)

    improvements = subparsers.add_parser(
        "improvements", help="list the improvements by name"
    )
    improvements.set_defaults(func=_cmd_improvements)

    one = subparsers.add_parser("one", help="run one suite once")
    one.add_argument("--suite", required=True, choices=sorted(SUITES))
    one.add_argument("--improvement", choices=sorted(IMPROVEMENTS), default=None)
    one.add_argument("--model", default=DEFAULT_MODEL)
    one.add_argument("--timeout", type=int, default=600)
    one.set_defaults(func=_cmd_one)

    batch = subparsers.add_parser(
        "batch", help="run attempts until the checkpoint holds --target of them"
    )
    batch.add_argument("--suite", required=True, choices=sorted(SUITES))
    batch.add_argument("--target", type=int, default=16)
    batch.add_argument("--improvement", choices=sorted(IMPROVEMENTS), default=None)
    batch.add_argument("--model", default=DEFAULT_MODEL)
    batch.add_argument("--timeout", type=int, default=600)
    batch.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="checkpoint path (default: ~/evidence/<suite>-<date>.jsonl)",
    )
    batch.set_defaults(func=_cmd_batch)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
