# Phase 8 — Eval CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the eval harness a documented, stdlib-only entry point — `uv run python -m harness.cli` — where suites and improvements are addressed by name, failures say what to fix, and `--help` is the documentation.

**Architecture:** Two new public surfaces and one new file. `harness/runner.py` gains two name registries (`SUITES`, `IMPROVEMENTS`) so a short name resolves a `Suite` value or an `Improvement` factory. `harness/cli.py` is a single argparse module with six subcommands (`one`, `batch`, `preflight`, `suites`, `improvements`, `summarize`) that translate what `run_suite`/`run_batch` already do — the engine is untouched. The CLI's known failure classes (`ModelServerDown`, the version `RuntimeError`, the checkpoint `ValueError`) are rendered as fixable sentences with exit code 2, never tracebacks. `summarize` reads a checkpoint and compares nothing.

**Tech Stack:** Python 3.14, stdlib `argparse` only (nothing added to `pyproject.toml`), pytest for the hermetic test suite, existing `harness/*` modules as-is.

**Spec:** [`../specs/2026-08-13-phase8-eval-cli-design.md`](../specs/2026-08-13-phase8-eval-cli-design.md)

**Worktree:** Work happens in the `.worktrees/phase8-eval-cli` worktree, on branch `phase8-eval-cli` branched from `main` at `d3aee12` (which carries the design spec). Do not work in the main checkout; do not touch phase 7 machinery or its branches.

## Global Constraints

- Python `>=3.14,<3.15`, uv-managed. Never activate `.venv` by hand; prefix every command with `uv run`.
- **Stdlib only.** New code uses `argparse`, `datetime`, `subprocess`, `collections.abc` — nothing may be added to `pyproject.toml` dependencies.
- Quality gates, all three must pass before any commit: `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check`.
- Full suite before any commit: `uv run pytest` — currently 495 passed, 4 skipped (live tests skip without `SATYRN_LIVE=1`). Skips are expected; failures are not.
- Ruff lint selects `E`, `F`, `I`, `UP`, `B`, `SIM`; `E501` (line length) is ignored. Import sorting is enforced — keep imports in one block at the top.
- `pyrefly` type-checks `harness`, `tests`, `tools`. Annotate every public function signature.
- **Test-first.** Every task writes the failing test first, watches it fail, implements, watches it pass. No test, no code.
- `import harness.runner` must not fail on a machine without Pi. The improvement factories call `pi_package_root()`, so `IMPROVEMENTS` holds the factories (callables), never their results.
- No manifest, no Makefile/Justfile target, no comparison automation. The `Improvement` docstring parks the manifest cycle.
- Commit messages in repo style (`feat(phase8): …`, `docs(phase8): …`), each ending with the repo's agent-commit trailer:
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`
- One commit per cycle, in order. If a cycle's gate fails, fix within the cycle, never by weakening a test.

---

## File Structure

| File | Responsibility |
|---|---|
| `harness/runner.py` | Modify. Add `SUITES` and `IMPROVEMENTS` name registries; rename the `IMPROVEMENTS` Path constant to `IMPROVEMENTS_DIR`. |
| `harness/cli.py` | Create. The argparse entry point: six subcommands, registry resolution, friendly error translation. No engine changes. |
| `tests/test_registries.py` | Create. Registry contract: exact key sets, resolvable values, import-time laziness. |
| `tests/test_cli.py` | Create. CLI behavior, hermetic: subcommand output, arg validation, refusals, summarize shape. |
| `README.md` | Modify. A "Run an eval" subsection with `one`/`batch` one-liners pointing at `docs/evals.md`. |
| `docs/evals.md` | Create. The longer treatment: why measure, run/batch/improvement/checkpoint, how to run each, the three gotchas. |
| `docs/index.md` | Modify. Add `evals` to the "Getting started" toctree. |

---

### Task 1: Name registries (Cycle 1)

**Files:**
- Modify: `harness/runner.py` (imports ~line 1-7; `IMPROVEMENTS` at line 114; four references at lines 202, 206, 250, 275; insert after `DURATION` ~line 86; insert after `sdd_orchestrator_guarded_stack` ~line 279)
- Create: `tests/test_registries.py`

**Interfaces:**
- Consumes: the existing `Suite` dataclass, the three `Suite` constants (`AGENTCLINIC_PHASE_1`, `AGENTCLINIC_PHASE_1_USER_STORY`, `DURATION`), the `Improvement` dataclass, the four factory functions.
- Produces: `runner.SUITES: dict[str, Suite]`, `runner.IMPROVEMENTS: dict[str, Callable[[], Improvement]]`, `runner.IMPROVEMENTS_DIR: Path`. Task 2 consumes all three.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_registries.py`:

```python
"""The name registries: suites and improvements addressable by short name.

Phase 8 cycle 1. The registries are the mild step short of a manifest --
the `Improvement` docstring parks that cycle ("that is the cycle that adds
the manifest"). The critical constraint is laziness: `import
harness.runner` must not fail on a machine without Pi, so `IMPROVEMENTS`
holds the *factories*, never their results. The CLI resolves a name by
invoking the factory, exactly as callers invoke `tech_stack_only()` today.
"""

import importlib
from pathlib import Path

import pytest

import harness.runner as runner
from harness.runner import IMPROVEMENTS, SUITES


def test_suites_keys_are_the_documented_short_names():
    assert set(SUITES) == {"agentclinic-phase-1", "user-story", "duration"}


def test_improvements_keys_are_the_documented_short_names():
    assert set(IMPROVEMENTS) == {
        "tech-stack-only",
        "sdd-orchestrator",
        "sdd-orchestrator-guarded",
        "sdd-orchestrator-guarded-stack",
    }


def test_every_suite_resolves_to_files_that_exist():
    for key, suite in SUITES.items():
        assert suite.task_spec.is_file(), f"{key}: {suite.task_spec}"
        assert suite.acceptance.is_file(), f"{key}: {suite.acceptance}"
        assert suite.source_allowlist, f"{key}: empty allowlist"


def test_improvements_hold_factories_not_instances():
    for key, factory in IMPROVEMENTS.items():
        assert callable(factory), f"{key}: {factory!r} is not callable"
        assert not isinstance(factory, runner.Improvement)


def test_every_improvement_resolves_to_its_keyed_name(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "pi_package_root", lambda: tmp_path)
    for key, factory in IMPROVEMENTS.items():
        improvement = factory()
        assert isinstance(improvement, runner.Improvement)
        assert improvement.name == key


def test_import_never_resolves_pi(monkeypatch):
    """The constraint the registry exists to serve: importing the harness
    must not fail on a machine without Pi, and resolving an improvement is
    the moment Pi is touched -- never before."""

    def broken() -> Path:
        raise AssertionError("pi_package_root must not run at import time")

    monkeypatch.setattr(runner, "pi_package_root", broken)
    # Reload re-executes the module body with pi_package_root broken. If
    # import-time code called it, this reload would raise right here.
    reloaded = importlib.reload(runner)
    # Reload redefined pi_package_root to the original; re-patch so the
    # laziness claim below is about the reloaded module.
    monkeypatch.setattr(reloaded, "pi_package_root", broken)
    assert reloaded.IMPROVEMENTS["tech-stack-only"] is reloaded.tech_stack_only
    with pytest.raises(AssertionError, match="must not run at import time"):
        reloaded.IMPROVEMENTS["tech-stack-only"]()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_registries.py -v`
Expected: FAIL — `AttributeError: module 'harness.runner' has no attribute 'SUITES'` (the dicts do not exist yet).

- [ ] **Step 3: Implement the registries in `harness/runner.py`**

Edit 1 — imports. Replace:

```python
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
```

with:

```python
import hashlib
import json
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
```

Edit 2 — rename the Path constant (line 114). Replace:

```python
IMPROVEMENTS = REPO_ROOT / "improvements"
```

with:

```python
IMPROVEMENTS_DIR = REPO_ROOT / "improvements"
```

Edit 3 — update the four references inside the factories (lines 202, 206, 250, 275), replacing every `IMPROVEMENTS / ` with `IMPROVEMENTS_DIR / `:
- line 202: `seed_dir=IMPROVEMENTS / "sdd-orchestrator" / "seed",`
- line 206: `system_prompt=IMPROVEMENTS / "sdd-orchestrator" / "orchestrator.md",`
- line 250: `system_prompt=IMPROVEMENTS / "tech-stack-only" / "stack.md",`
- line 275: `system_prompt=IMPROVEMENTS / "sdd-orchestrator" / "orchestrator-with-stack.md",`

Edit 4 — insert `SUITES` after the `DURATION` suite definition (the `)` that closes `DURATION` at ~line 86, immediately before `@dataclass(frozen=True)\nclass Improvement:`):

```python
SUITES: dict[str, Suite] = {
    # Keys are CLI-facing short names, not mirrors of `Suite.name`: the
    # user-story suite's real name is `agentclinic-phase-1-user-story`,
    # and nobody should have to type it. The shorthand is safe because
    # `Suite.name` is not recorded in `RunConditions` -- a checkpoint
    # distinguishes suites by task_spec_sha256/acceptance_sha256/
    # source_allowlist -- so it cannot drift recorded evidence.
    "agentclinic-phase-1": AGENTCLINIC_PHASE_1,
    "user-story": AGENTCLINIC_PHASE_1_USER_STORY,
    "duration": DURATION,
}
```

Edit 5 — insert `IMPROVEMENTS` after `sdd_orchestrator_guarded_stack()` (the `)` closing that factory at ~line 279, immediately before `@dataclass(frozen=True)\nclass RunConditions:`):

```python
IMPROVEMENTS: dict[str, Callable[[], Improvement]] = {
    # Values are the *factories*, never their results: they call
    # pi_package_root(), and calling it at import time would break
    # `import harness.runner` on a machine without Pi. The CLI resolves
    # a name by invoking the factory, exactly as callers invoke
    # tech_stack_only() today. Keys mirror `Improvement.name` exactly
    # because improvement_name *is* recorded in RunConditions -- the
    # name a user types is the name in the checkpoint.
    "tech-stack-only": tech_stack_only,
    "sdd-orchestrator": sdd_orchestrator,
    "sdd-orchestrator-guarded": sdd_orchestrator_guarded,
    "sdd-orchestrator-guarded-stack": sdd_orchestrator_guarded_stack,
}
```

- [ ] **Step 4: Run the registry tests to verify they pass**

Run: `uv run pytest tests/test_registries.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Confirm no regression and run the quality gates**

Run: `uv run pytest` — Expected: 501 passed, 4 skipped (the six new tests added to 495).
Run: `uv run ruff check .` — Expected: clean.
Run: `uv run ruff format --diff` — Expected: no diff.
Run: `uv run pyrefly check` — Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add harness/runner.py tests/test_registries.py
git commit -m "feat(phase8): name the suites and improvements

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: The CLI skeleton (Cycle 2)

**Files:**
- Create: `harness/cli.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Consumes: `runner.SUITES`, `runner.IMPROVEMENTS`, `runner.IMPROVEMENTS_DIR`, `run_suite(suite, *, model=DEFAULT_MODEL, timeout=600, improvement=None) -> RunResult`, `run_batch(checkpoint_path, *, suite, target=16, model=DEFAULT_MODEL, improvement=None, timeout=600) -> list[RunResult]`, `RunResult.accepted`, `GradeResult` fields, `DEFAULT_MODEL`.
- Produces: `cli.main(argv: Sequence[str] | None = None) -> int` (subcommands `suites`, `improvements`, `one`, `batch`), `cli._rejection_reasons(result: RunResult) -> list[str]`. Task 3 extends `main` with exception translation; Task 4 adds `summarize`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cli.py`:

```python
"""The Phase 8 eval CLI: suites and improvements by name, friendly failures.

Cycles 2-4. Hermetic: nothing here invokes Pi or a model. `run_suite` and
`run_batch` are stubbed where they would otherwise reach out; the CLI's own
liveness/version checks are stubbed in the cycle-3 tests.
"""

from datetime import date
from pathlib import Path

import pytest

from harness import cli
from harness.grading import GradeResult
from harness.runner import RunConditions, RunResult, SUITES
from tests.support import make_conditions


def _result(
    accepted: bool = True,
    conditions: RunConditions | None = None,
    pi_timed_out: bool = False,
    **grade_overrides,
) -> RunResult:
    """A synthetic run result: accepted by default, signals overridable.

    `grade_overrides` reaches `GradeResult` (e.g. `refused_config`,
    `timed_out`); `pi_timed_out` is a `RunResult` field and must not.
    """
    grade = GradeResult(
        accepted=accepted,
        tests_executed=4,
        tests_expected=4,
        returncode=0,
        stdout="",
        stderr="",
        refused_config=(),
        **grade_overrides,
    )
    return RunResult(
        diff="",
        grade=grade,
        pi_stdout="",
        pi_stderr="",
        pi_returncode=0,
        pi_timed_out=pi_timed_out,
        conditions=conditions if conditions is not None else make_conditions(),
    )


def test_help_lists_the_cli_subcommands(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for name in ("one", "batch", "suites", "improvements"):
        assert name in out


def test_suites_lists_each_key_beside_its_suite_name(capsys):
    assert cli.main(["suites"]) == 0
    out = capsys.readouterr().out
    for key, suite in SUITES.items():
        assert f"{key} ({suite.name})" in out


def test_improvements_lists_the_keys(capsys):
    assert cli.main(["improvements"]) == 0
    out = capsys.readouterr().out
    for key in cli.IMPROVEMENTS:
        assert key in out


def test_unknown_suite_is_an_argparse_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["one", "--suite", "no-such-suite"])
    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_unknown_improvement_is_an_argparse_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["one", "--suite", "duration", "--improvement", "no-such"])
    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_one_prints_an_accepted_verdict(monkeypatch, capsys):
    monkeypatch.setattr(
        cli, "run_suite", lambda suite, **kwargs: _result(accepted=True)
    )
    assert cli.main(["one", "--suite", "duration"]) == 0
    assert "accepted: 4/4 tests passed" in capsys.readouterr().out


def test_one_prints_the_signal_behind_a_rejection(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "run_suite",
        lambda suite, **kwargs: _result(
            accepted=False, refused_config=("pyproject.toml",)
        ),
    )
    assert cli.main(["one", "--suite", "duration"]) == 0
    assert "rejected: refused_config=pyproject.toml" in capsys.readouterr().out


def test_one_forwards_improvement_model_and_timeout(monkeypatch, capsys):
    seen = {}

    def fake_run_suite(suite, **kwargs):
        seen.update(kwargs)
        return _result(accepted=True)

    monkeypatch.setattr(cli, "run_suite", fake_run_suite)
    assert (
        cli.main(
            [
                "one",
                "--suite",
                "duration",
                "--improvement",
                "tech-stack-only",
                "--model",
                "some-model",
                "--timeout",
                "30",
            ]
        )
        == 0
    )
    assert seen["model"] == "some-model"
    assert seen["timeout"] == 30
    assert seen["improvement"] is not None
    assert seen["improvement"].name == "tech-stack-only"


def test_batch_uses_the_default_checkpoint_path(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    captured = {}

    def fake_run_batch(checkpoint_path, **kwargs):
        captured["checkpoint"] = checkpoint_path
        captured["kwargs"] = kwargs
        return [_result(accepted=True)]

    monkeypatch.setattr(cli, "run_batch", fake_run_batch)
    assert cli.main(["batch", "--suite", "duration", "--target", "1"]) == 0
    expected = tmp_path / "evidence" / f"duration-{date.today().isoformat()}.jsonl"
    assert captured["checkpoint"] == expected
    assert captured["kwargs"]["target"] == 1


def test_batch_prints_attempts_and_summary(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(
        cli,
        "run_batch",
        lambda checkpoint_path, **kwargs: [
            _result(accepted=True),
            _result(accepted=False, timed_out=True, pi_timed_out=True),
        ],
    )
    assert cli.main(["batch", "--suite", "duration"]) == 0
    out = capsys.readouterr().out
    assert "run 1: accepted" in out
    assert "run 2: rejected (timed_out)" in out
    assert "batch complete: 1/2 accepted" in out


def test_negative_target_is_refused(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "run_batch",
        lambda *args, **kwargs: pytest.fail("run_batch must not run"),
    )
    assert cli.main(["batch", "--suite", "duration", "--target", "-1"]) == 2
    assert "must not be negative" in capsys.readouterr().err
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.cli'`.

- [ ] **Step 3: Implement `harness/cli.py` (skeleton)**

Create `harness/cli.py`:

```python
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
        reasons.append(
            f"tests_executed {grade.tests_executed}/{grade.tests_expected}"
        )
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
            Path.home()
            / "evidence"
            / f"{args.suite}-{date.today().isoformat()}.jsonl"
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
```

- [ ] **Step 4: Run the CLI tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS (10 passed).

- [ ] **Step 5: Confirm no regression and run the quality gates**

Run: `uv run pytest` — Expected: 511 passed, 4 skipped.
Run: `uv run ruff check .` — Expected: clean.
Run: `uv run ruff format --diff` — Expected: no diff.
Run: `uv run pyrefly check` — Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add harness/cli.py tests/test_cli.py
git commit -m "feat(phase8): add the eval CLI entry point

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: Friendly preflight (Cycle 3)

**Files:**
- Modify: `harness/cli.py` — add imports; add `MODEL_SERVER_FIX`; add `check_model_server_alive()` calls in `_cmd_one`/`_cmd_batch`; add `_cmd_preflight`; register `preflight`; wrap `main`'s dispatch in exception translation.
- Modify: `tests/test_cli.py` — add imports (`SimpleNamespace`, `ModelServerDown`); append cycle-3 tests.

**Interfaces:**
- Consumes: `harness.liveness.check_model_server_alive`, `harness.liveness.ModelServerDown`, `harness.runner.EXPECTED_PI_VERSION`.
- Produces: the `preflight` subcommand; `main` now returns 2 with a fixable sentence on `ModelServerDown`, the version `RuntimeError`, and the checkpoint `ValueError`. Task 4's `summarize` relies on `main`'s translation staying in place.

- [ ] **Step 1: Write the failing tests**

First, update the five cycle-2 tests that exercise `one`/`batch` to stub the
liveness check: cycle 3 adds the real `check_model_server_alive()` call to
`_cmd_one`/`_cmd_batch`, and without a stub those tests would make a real
socket call to `127.0.0.1:8001` (nondeterministic — something could be
listening). Add this line as the first statement of each of these five
functions in `tests/test_cli.py`:

```python
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
```

- `test_one_prints_an_accepted_verdict`
- `test_one_prints_the_signal_behind_a_rejection`
- `test_one_forwards_improvement_model_and_timeout`
- `test_batch_uses_the_default_checkpoint_path`
- `test_batch_prints_attempts_and_summary`

(`test_negative_target_is_refused` needs no stub: `_cmd_batch` checks
`--target` before it checks liveness, so that test returns before any
socket call.)

Then append the cycle-3 tests to `tests/test_cli.py`:

```python
def test_one_dead_server_is_a_friendly_refusal(monkeypatch, capsys):
    def down():
        raise ModelServerDown(
            "model server not reachable at http://127.0.0.1:8001/v1/models"
        )

    monkeypatch.setattr(cli, "check_model_server_alive", down)
    assert cli.main(["one", "--suite", "duration"]) == 2
    err = capsys.readouterr().err
    assert "omlx start" in err
    assert "Traceback" not in err


def test_batch_version_mismatch_is_a_friendly_refusal(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)

    def wrong_version(*args, **kwargs):
        raise RuntimeError("this harness pins Pi 0.84.1, but 0.83.0 is installed")

    monkeypatch.setattr(cli, "run_batch", wrong_version)
    assert cli.main(["batch", "--suite", "duration"]) == 2
    err = capsys.readouterr().err
    assert "refused:" in err
    assert "pins Pi 0.84.1" in err
    assert "Traceback" not in err


def test_batch_checkpoint_mismatch_is_a_friendly_refusal(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)

    def mismatch(*args, **kwargs):
        raise ValueError("checkpoint conditions do not match this batch")

    monkeypatch.setattr(cli, "run_batch", mismatch)
    assert cli.main(["batch", "--suite", "duration"]) == 2
    err = capsys.readouterr().err
    assert "checkpoint conditions do not match" in err
    assert "Traceback" not in err


class _FakeSubprocess:
    def __init__(self, stdout: str):
        self._stdout = stdout

    def run(self, command, **kwargs):
        return SimpleNamespace(stdout=self._stdout, stderr="", returncode=0)


def test_preflight_reports_ok(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(cli, "subprocess", _FakeSubprocess("0.84.1\n"))
    assert cli.main(["preflight"]) == 0
    out = capsys.readouterr().out
    assert "model server: OK" in out
    assert "pi version: OK (0.84.1)" in out


def test_preflight_reports_a_wrong_pi_version(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(cli, "subprocess", _FakeSubprocess("0.83.0\n"))
    assert cli.main(["preflight"]) == 2
    err = capsys.readouterr().err
    assert "docs/setup.md" in err


def test_preflight_reports_a_dead_server(monkeypatch, capsys):
    def down():
        raise ModelServerDown("model server not reachable")

    monkeypatch.setattr(cli, "check_model_server_alive", down)
    monkeypatch.setattr(cli, "subprocess", _FakeSubprocess("0.84.1\n"))
    assert cli.main(["preflight"]) == 2
    out = capsys.readouterr().out
    assert "model server: DOWN" in out
```

Update the import block at the top of `tests/test_cli.py` to add `from types import SimpleNamespace` (before `import pytest`, keeping the stdlib block together) and add `from harness.liveness import ModelServerDown` to the `from harness import cli` line's neighborhood:

```python
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from harness import cli
from harness.grading import GradeResult
from harness.liveness import ModelServerDown
from harness.runner import RunConditions, RunResult, SUITES
from tests.support import make_conditions
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `AttributeError: module 'harness.cli' has no attribute 'check_model_server_alive'` (the CLI does not import it yet, and `preflight` does not exist).

- [ ] **Step 3: Implement the friendly translation in `harness/cli.py`**

Edit 1 — imports. Replace:

```python
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
```

with:

```python
import argparse
import subprocess
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from harness.liveness import ModelServerDown, check_model_server_alive
from harness.pi_invocation import DEFAULT_MODEL
from harness.runner import (
    EXPECTED_PI_VERSION,
    IMPROVEMENTS,
    SUITES,
    Improvement,
    RunResult,
    run_batch,
    run_suite,
)
```

Edit 2 — add the fix sentence after the exit-code constants:

```python
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_REFUSED = 2

MODEL_SERVER_FIX = "Start the model server with `omlx start` (see docs/setup.md)."
```

Edit 3 — add the liveness check to `_cmd_one`. Replace:

```python
def _cmd_one(args: argparse.Namespace) -> int:
    result = run_suite(
```

with:

```python
def _cmd_one(args: argparse.Namespace) -> int:
    check_model_server_alive()
    result = run_suite(
```

Edit 4 — add the liveness check to `_cmd_batch`. Replace:

```python
    if args.target < 0:
        print("refused: --target must not be negative", file=sys.stderr)
        return EXIT_REFUSED
    checkpoint = args.checkpoint
```

with:

```python
    if args.target < 0:
        print("refused: --target must not be negative", file=sys.stderr)
        return EXIT_REFUSED
    check_model_server_alive()
    checkpoint = args.checkpoint
```

Edit 5 — add `_cmd_preflight` after `_cmd_batch` (before `def _build_parser`):

```python
def _cmd_preflight(args: argparse.Namespace) -> int:
    lines = []
    ok = True
    try:
        check_model_server_alive()
        lines.append("model server: OK")
    except ModelServerDown as error:
        lines.append(f"model server: DOWN ({error})")
        ok = False
    version = ""
    try:
        completed = subprocess.run(
            ["pi", "--version"], capture_output=True, text=True, check=False
        )
        version = (completed.stdout or completed.stderr).strip()
    except OSError:
        version = ""
    if version == EXPECTED_PI_VERSION:
        lines.append(f"pi version: OK ({version})")
    else:
        shown = version or "<pi not found>"
        lines.append(
            f"pi version: MISMATCH (installed {shown!r}, expected {EXPECTED_PI_VERSION})"
        )
        ok = False
    print("\n".join(lines))
    if not ok:
        print(f"Fix: {MODEL_SERVER_FIX} For Pi, see docs/setup.md.", file=sys.stderr)
        return EXIT_REFUSED
    return EXIT_OK
```

Edit 6 — register `preflight` in `_build_parser`. After the `batch` block, before `return parser`:

```python
    preflight = subparsers.add_parser(
        "preflight", help="check the model server and the pinned Pi version"
    )
    preflight.set_defaults(func=_cmd_preflight)

    return parser
```

Edit 7 — wrap `main`'s dispatch in exception translation. Replace:

```python
def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
```

with:

```python
def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ModelServerDown as error:
        print(f"refused: {error}\n{MODEL_SERVER_FIX}", file=sys.stderr)
        return EXIT_REFUSED
    except (RuntimeError, ValueError) as error:
        print(f"refused: {error}", file=sys.stderr)
        return EXIT_REFUSED
```

(The version `RuntimeError`'s own message already names `docs/setup.md`; the checkpoint `ValueError` is rendered as-is. Both are "refused before starting", exit 2. A genuine unexpected exception still tracebacks — a bug should be visible.)

- [ ] **Step 4: Run the CLI tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS (16 passed).

- [ ] **Step 5: Confirm no regression and run the quality gates**

Run: `uv run pytest` — Expected: 517 passed, 4 skipped.
Run: `uv run ruff check .` — Expected: clean.
Run: `uv run ruff format --diff` — Expected: no diff.
Run: `uv run pyrefly check` — Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add harness/cli.py tests/test_cli.py
git commit -m "feat(phase8): translate refusals into fixable sentences

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: `summarize` (Cycle 4)

**Files:**
- Modify: `harness/cli.py` — add `load_checkpoint` import; add `_cmd_summarize`; register `summarize`.
- Modify: `tests/test_cli.py` — add imports (`json`, `asdict`); add `_write_checkpoint` helper; append cycle-4 tests.

**Interfaces:**
- Consumes: `harness.checkpoint.load_checkpoint(path: Path) -> list[RunResult]` (returns `[]` for a missing file — but `summarize` refuses a missing path itself, because for a *reader* an empty result usually means a typo); `GradeResult` fields; `RunConditions` fields (`model`, `improvement_name`, `pi_version`).
- Produces: the `summarize` subcommand. Task 5 documents it.

- [ ] **Step 1: Write the failing tests**

Add `json` and `asdict` to the imports in `tests/test_cli.py` (stdlib block becomes):

```python
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from types import SimpleNamespace
```

Add the helper after `_result`:

```python
def _write_checkpoint(path: Path, results: list[RunResult]) -> None:
    """Write records the same way append_checkpoint would."""
    path.write_text(
        "\n".join(json.dumps(asdict(result)) for result in results) + "\n"
    )
```

Append the cycle-4 tests:

```python
def test_help_lists_all_six_subcommands(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for name in (
        "one",
        "batch",
        "preflight",
        "suites",
        "improvements",
        "summarize",
    ):
        assert name in out


def test_summarize_prints_conditions_acceptance_and_rejections(capsys, tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    records = [
        _result(
            accepted=True,
            conditions=make_conditions(
                model="m", improvement_name="none", pi_version="0.84.1"
            ),
        ),
        _result(accepted=False, refused_config=("pyproject.toml",)),
        _result(accepted=False, timed_out=True, pi_timed_out=True),
    ]
    _write_checkpoint(path, records)
    assert cli.main(["summarize", str(path)]) == 0
    out = capsys.readouterr().out
    assert "runs:       3" in out
    assert "accepted:   1" in out
    assert "conditions: model=m  improvement=none  pi=0.84.1" in out
    assert "2   refused_config=pyproject.toml" in out
    assert "3   timed_out" in out


def test_summarize_reports_a_missing_checkpoint(capsys, tmp_path):
    missing = tmp_path / "nope.jsonl"
    assert cli.main(["summarize", str(missing)]) == 2
    err = capsys.readouterr().err
    assert "no such checkpoint" in err
    assert "Traceback" not in err


def test_summarize_reads_an_empty_checkpoint(capsys, tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("")
    assert cli.main(["summarize", str(path)]) == 0
    out = capsys.readouterr().out
    assert "runs:       0" in out
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `invalid choice: 'summarize'` / `SystemExit: 2` (the subcommand does not exist yet).

- [ ] **Step 3: Implement `summarize` in `harness/cli.py`**

Edit 1 — import. In the imports block, add `from harness.checkpoint import load_checkpoint` before the `from harness.liveness import ...` line:

```python
from harness.checkpoint import load_checkpoint
from harness.liveness import ModelServerDown, check_model_server_alive
```

Edit 2 — add `_cmd_summarize` after `_cmd_preflight` (before `def _build_parser`):

```python
def _cmd_summarize(args: argparse.Namespace) -> int:
    path = args.checkpoint
    if not path.is_file():
        print(f"refused: no such checkpoint: {path}", file=sys.stderr)
        return EXIT_REFUSED
    results = load_checkpoint(path)
    print(f"file:       {path}")
    if not results:
        print("runs:       0")
        return EXIT_OK
    conditions = results[0].conditions
    if conditions is None:
        print("conditions: <none recorded>")
    else:
        print(
            "conditions: "
            f"model={conditions.model}  "
            f"improvement={conditions.improvement_name}  "
            f"pi={conditions.pi_version}"
        )
    print(f"runs:       {len(results)}")
    accepted = sum(1 for result in results if result.accepted)
    print(f"accepted:   {accepted}")
    rejected = [
        (index, result)
        for index, result in enumerate(results, start=1)
        if not result.accepted
    ]
    if rejected:
        print()
        print("rejected:")
        for index, result in rejected:
            print(f"  {index:<3} {', '.join(_rejection_reasons(result))}")
    return EXIT_OK
```

Edit 3 — register `summarize` in `_build_parser`, after the `preflight` block, before `return parser`:

```python
    summarize = subparsers.add_parser(
        "summarize",
        help="summarize a checkpoint; reads it and compares nothing",
    )
    summarize.add_argument("checkpoint", type=Path)
    summarize.set_defaults(func=_cmd_summarize)

    return parser
```

- [ ] **Step 4: Run the CLI tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS (20 passed).

- [ ] **Step 5: Confirm no regression and run the quality gates**

Run: `uv run pytest` — Expected: 521 passed, 4 skipped.
Run: `uv run ruff check .` — Expected: clean.
Run: `uv run ruff format --diff` — Expected: no diff.
Run: `uv run pyrefly check` — Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add harness/cli.py tests/test_cli.py
git commit -m "feat(phase8): summarize a checkpoint without comparing

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 5: Documentation (Cycle 5)

**Files:**
- Modify: `README.md` — add a "Run an eval" subsection; add a row to the "Where to go next" table.
- Create: `docs/evals.md`
- Modify: `docs/index.md` — add `evals` to the "Getting started" toctree.

**Interfaces:**
- Consumes: the final CLI surface from Tasks 2-4 (six subcommands, `--help` as documentation, exit codes 0/1/2).
- Produces: `docs/evals.md` and the README pointers — the phase's definition of done ("a contributor can run `uv run python -m harness.cli --help` and get from zero to a batch with no reference to `harness/runner.py`").

- [ ] **Step 1: Write the README section**

In `README.md`, insert a new section between "Try one attempt on your own repository" and "What the evidence actually says":

````markdown
## Run an eval

The harness that produced the evidence below is driven by a small command —
suites and improvements by name, not Python constants:

```bash
uv run python -m harness.cli one --suite duration
uv run python -m harness.cli batch --suite duration --improvement tech-stack-only
```

`one` runs a single attempt; `batch` runs attempts until the checkpoint
holds `--target` of them (default 16). `suites` and `improvements` list
what exists, `preflight` checks the model server and the pinned Pi version,
and `summarize <checkpoint.jsonl>` reads a checkpoint without comparing
anything — comparison stays manual. `--help` is the documentation.

What a run, batch, improvement, and checkpoint are — and the three things
that will bite you — is in [evals.md](docs/evals.md).
````

In the "Where to go next" table, add a row after the evidence-index row:

```markdown
| Run an eval | [evals.md](docs/evals.md) |
```

- [ ] **Step 2: Write `docs/evals.md`**

Create `docs/evals.md`:

````markdown
# Running evals

Every number this project publishes comes from the harness: a small local
model (Pi driving oMLX) is given a task, its workspace is graded against a
fixed acceptance contract, and the verdict is recorded. The one-liners are
in the [README](../README.md); this page is the longer treatment.

## Why measure

Small models are stochastic. A single run tells you almost nothing — the
interesting question is whether a *technique* (a prompt structure, an
improvement) reliably helps. So the harness repeats a run until it has a
checkpoint full of attempts, and the acceptance rate across those attempts
is the number you can compare. The comparison itself stays manual and
deliberate: one improvement at a time, side by side, by hand.

## The four concepts

**A run** is one model invocation against one suite. The harness checks the
model server, prepares an empty workspace, invokes Pi with the suite's task
spec, copies the model's allowlisted files into a fresh directory, and runs
the suite's acceptance tests there. A run is accepted only if Pi exited 0,
did not time out, and every acceptance test passed.

**A batch** is a sequence of runs that continues until the checkpoint holds
`--target` of them (default 16). A batch is *resumable*: it records each
run's conditions (model, Pi version, digests of the task spec, acceptance
file, and extensions) and refuses to resume a checkpoint whose conditions
have changed — so a batch and a checkpoint are locked together.

**An improvement** is a named, optional change to how a run is steered: a
seeded specialist, an extra extension, a system prompt. A run has exactly
one improvement or none. Improvements exist so two arms of a comparison
differ in one thing at a time.

**A checkpoint** is a JSONL file, one run per line, under `~/evidence/` by
default. It is the durable record of a batch — raw stdout, the diff, the
grade verdict, and the conditions the run happened under. `summarize`
reads it; nothing else in the CLI writes it.

## How to run each

```bash
uv run python -m harness.cli suites            # what can I run?
uv run python -m harness.cli improvements      # what can I apply?
uv run python -m harness.cli preflight         # is the server up? the right Pi?
uv run python -m harness.cli one --suite duration
uv run python -m harness.cli batch --suite duration --improvement tech-stack-only
uv run python -m harness.cli summarize ~/evidence/duration-2026-08-13.jsonl
```

`--help` on any subcommand is the documentation. Exit codes follow the
project's convention: 0 the command completed its purpose, 2 refused before
starting (unknown name, dead server, wrong Pi version, checkpoint
mismatch), 1 an unexpected error.

## The three things that will bite you

1. **Batches are single-threaded.** The model server serializes children,
   so a batch of 16 is 16 sequential runs — plan for it to take a while,
   and never run two batches against the same server expecting speed.

2. **A commit aborts a running batch.** A batch records the harness
   revision as a run condition and refuses to resume a checkpoint whose
   conditions moved. If you commit mid-batch, the next attempt dies with a
   checkpoint-mismatch refusal and you must start that checkpoint fresh.

3. **There is no trustworthy wall-clock number.** Per-message durations are
   not recorded as start/end pairs, and this phase publishes no timing
   claim. If you see a wall-clock figure anywhere in this project's
   history, treat it as suspect.
````

- [ ] **Step 3: Wire the new doc into the docs site**

In `docs/index.md`, add `evals` to the "Getting started" toctree:

````markdown
```{toctree}
:maxdepth: 1
:caption: Getting started

setup
contributing
glossary
loop-breaker
evals
```
````

- [ ] **Step 4: Verify the docs build**

Run: `uv run --group docs sphinx-build -W -b html docs docs/_build/html`
Expected: exit 0, no warnings raised as errors. (If `sphinx-build` is not
on PATH in the venv, run `uv run --group docs python -m sphinx -W -b html docs docs/_build/html`.)

- [ ] **Step 5: Verify the definition of done end to end**

Run: `uv run python -m harness.cli --help` — Expected: lists all six subcommands.
Run: `uv run python -m harness.cli suites` — Expected: the three suites, each with its `Suite.name` in parentheses.
Run: `uv run python -m harness.cli preflight` — Expected: a report of the model server and Pi version (either OK lines or a fix sentence with exit 2). This is the one command that touches the real environment; the model server may legitimately be down, in which case the friendly refusal *is* the verification.
Run: `uv run pytest` — Expected: 521 passed, 4 skipped (unchanged; docs are not tested).
Run: `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check` — Expected: all clean.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/evals.md docs/index.md
git commit -m "docs(phase8): document the eval entry point

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Definition of Done

All five tasks committed on `phase8-eval-cli` with the full suite green
(521 passed, 4 skipped) and all three quality gates clean:

- `uv run pytest`
- `uv run ruff check .`
- `uv run ruff format --diff`
- `uv run pyrefly check`

A contributor can run `uv run python -m harness.cli --help` and get from
zero to a batch with no reference to `harness/runner.py`. `docs/evals.md`
exists and the README points at it. The engine (`run_suite`/`run_batch`)
is byte-identical except for the two registry dicts added to `runner.py`.
