"""Candidate delivery, tested without a model or a network.

The model call is injected, so every branch of the lifecycle is
exercised deterministically. That is what makes the acceptance criteria
checkable on every change rather than only after a live run: the
expensive part of this flow is the one part that carries no logic.

The properties under test are the ones the roadmap names: the live
repository is never mutated, failure leaves no worktree or branch
behind, success leaves a readable ref, and stale or dirty live state
causes refusal rather than a copy.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from harness.candidate import (
    CANDIDATE_NAMESPACE,
    DeliveryRefused,
    deliver,
    preflight,
)
from harness.processes import ProcessResult
from harness.workspace import GIT_ENV


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, env=GIT_ENV
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "live"
    root.mkdir()
    _git(root, "init", "-q")
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("VALUE = 1\n")
    (root / "check.py").write_text(
        "import sys\nsys.path.insert(0, 'src')\n"
        "from app import VALUE\nsys.exit(0 if VALUE == 2 else 1)\n"
    )
    _git(root, "add", "-A")
    _git(
        root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base"
    )
    return root


def _writer(text: str, path: str = "src/app.py"):
    def run_model(worktree: Path) -> ProcessResult:
        target = worktree / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        return ProcessResult(0, "", "", timed_out=False)

    return run_model


def _noop(worktree: Path) -> ProcessResult:
    return ProcessResult(0, "", "", timed_out=False)


# sys.executable rather than "python": the interpreter running the
# tests is the one guaranteed to exist.
VALIDATION = (sys.executable, "check.py")


def test_success_leaves_a_durable_ref_and_a_clean_live_tree(repo: Path) -> None:
    before = _git(repo, "rev-parse", "HEAD")
    receipt = deliver(
        repo,
        "raise-value",
        "make VALUE 2",
        _writer("VALUE = 2\n"),
        VALIDATION,
        writable=("src/**",),
    )
    assert receipt.outcome == "candidate-created"
    assert receipt.candidate_ref == f"{CANDIDATE_NAMESPACE}/raise-value"
    assert receipt.validation_exit == 0

    # The live tree is untouched: same HEAD, nothing modified, no worktree.
    assert _git(repo, "rev-parse", "HEAD") == before
    assert _git(repo, "status", "--porcelain") == ""
    assert "satyrn-worktrees" not in _git(repo, "worktree", "list")

    # The candidate is readable without checking anything out.
    assert "VALUE = 2" in _git(repo, "show", f"{receipt.candidate_commit}:src/app.py")
    assert receipt.candidate_commit != before


def test_failed_validation_discards_and_leaves_nothing(repo: Path) -> None:
    before = _git(repo, "rev-parse", "HEAD")
    receipt = deliver(
        repo,
        "wrong",
        "make VALUE 2",
        _writer("VALUE = 99\n"),
        VALIDATION,
        writable=("src/**",),
    )
    assert receipt.outcome == "discarded"
    assert receipt.validation_exit != 0
    assert receipt.refusal == "declared validation did not pass"
    assert receipt.candidate_ref == ""

    assert _git(repo, "rev-parse", "HEAD") == before
    assert _git(repo, "status", "--porcelain") == ""
    assert _git(repo, "branch", "--list", "satyrn/candidate/wrong") == ""
    assert "satyrn-worktrees" not in _git(repo, "worktree", "list")


def test_out_of_scope_is_discarded_before_validation(repo: Path) -> None:
    """Validation must not report on work nobody asked for.

    A candidate that wrote outside its bounds is discarded first, so the
    receipt never carries a validation result for a diff whose shape was
    already refused.
    """
    receipt = deliver(
        repo,
        "stray",
        "edit",
        _writer("x = 1\n", path="elsewhere.py"),
        VALIDATION,
        writable=("src/**",),
    )
    assert receipt.outcome == "discarded"
    assert receipt.out_of_scope == ("elsewhere.py",)
    assert receipt.validation_exit is None, "validation must not have run"
    assert _git(repo, "status", "--porcelain") == ""


def test_a_candidate_that_changed_nothing_is_discarded(repo: Path) -> None:
    receipt = deliver(
        repo, "empty", "do nothing", _noop, VALIDATION, writable=("src/**",)
    )
    assert receipt.outcome == "discarded"
    assert receipt.refusal == "candidate changed nothing"
    assert receipt.validation_exit is None


def test_a_failed_model_call_that_wrote_nothing_is_not_blamed_on_the_model(
    repo: Path,
) -> None:
    """The verdict a contributor sees first must be about the right thing.

    A dead server, an unresolvable model name, a missing Pi -- all of them
    end with an unchanged tree. Reported as `candidate changed nothing`
    that reads as a model which declined to act, and the reader goes
    looking at their prompt instead of their setup.
    """

    def failed(worktree: Path) -> ProcessResult:
        return ProcessResult(1, "", "model 'nope' not found", timed_out=False)

    receipt = deliver(repo, "dead", "p", failed, VALIDATION, writable=("src/**",))
    assert receipt.outcome == "infrastructure-failure"
    assert receipt.child_exit == 1
    assert "setup" in receipt.refusal
    assert receipt.validation_exit is None, "nothing was judged"
    assert _git(repo, "status", "--porcelain") == ""
    assert "satyrn-worktrees" not in _git(repo, "worktree", "list")


def test_a_timeout_with_a_live_server_is_a_model_failure_not_infrastructure(
    repo: Path,
) -> None:
    """The split that cost a batch on 2026-08-15.

    A model that spends its whole wall clock proposing no-op edits leaves
    the same evidence as a dead server: timed out, nothing on disk. Called
    an infrastructure failure, the batch driver voids and *retries* it --
    three 900s attempts per slot, ending in `void_exhausted` with no data,
    while the receipt blames a server that was up throughout. The Cycle 7
    pre-registration says exhausting the budget is a plain failure, so the
    misclassification silently corrupts denominators.
    """

    def stalled(worktree: Path) -> ProcessResult:
        return ProcessResult(-15, "", "", timed_out=True)

    receipt = deliver(
        repo,
        "stalled",
        "p",
        stalled,
        VALIDATION,
        writable=("src/**",),
        server_probe=lambda: True,
    )
    assert receipt.outcome == "discarded", "must count, not void"
    assert receipt.child_timed_out is True
    assert "time budget" in receipt.refusal
    # The misdirection that mattered was the *instruction*, not the word:
    # the old text sent the reader off to check a server that was fine.
    assert "check that the model server is running" not in receipt.refusal
    assert receipt.validation_exit is None, "nothing was written, so nothing judged"


def test_a_timeout_with_a_dead_server_is_still_infrastructure(repo: Path) -> None:
    """The other side, so the reclassification cannot swallow a real outage.

    This is the asymmetry that makes the probe safe to add: it may only
    ever turn infrastructure into a recorded model failure, never blame a
    model for an unreachable server.
    """

    def stalled(worktree: Path) -> ProcessResult:
        return ProcessResult(-15, "", "", timed_out=True)

    receipt = deliver(
        repo,
        "dead-and-slow",
        "p",
        stalled,
        VALIDATION,
        writable=("src/**",),
        server_probe=lambda: False,
    )
    assert receipt.outcome == "infrastructure-failure"
    assert "setup" in receipt.refusal


def test_a_nonzero_exit_that_did_not_time_out_is_never_reclassified(
    repo: Path,
) -> None:
    """A crash is not a stall, even with the server up.

    The probe is consulted only on a timeout. A child that died fast --
    unresolvable model name, missing Pi -- is a setup problem however
    healthy the server looks.
    """

    def crashed(worktree: Path) -> ProcessResult:
        return ProcessResult(1, "", "model 'nope' not found", timed_out=False)

    receipt = deliver(
        repo,
        "crashed",
        "p",
        crashed,
        VALIDATION,
        writable=("src/**",),
        server_probe=lambda: True,
    )
    assert receipt.outcome == "infrastructure-failure"


def test_an_unknown_base_url_keeps_the_old_classification(repo: Path) -> None:
    """No cell, no `base_url`, no probe -- and the old behaviour stands.

    The default probe answers False for anything it cannot confirm, so a
    caller that never supplied a server address is classified exactly as
    it was before this split existed. Pins the conservative default rather
    than trusting the docstring.
    """

    def stalled(worktree: Path) -> ProcessResult:
        return ProcessResult(-15, "", "", timed_out=True)

    receipt = deliver(repo, "no-url", "p", stalled, VALIDATION, writable=("src/**",))
    assert receipt.outcome == "infrastructure-failure"


def test_a_child_that_exited_zero_and_declined_is_still_the_model(repo: Path) -> None:
    """The other side of the same split, so the fix cannot swallow it.

    Exit 0 and an unchanged tree is a model that chose not to act. That is
    a real result and must keep its own name.
    """
    receipt = deliver(repo, "declined", "p", _noop, VALIDATION, writable=("src/**",))
    assert receipt.outcome == "discarded"
    assert receipt.refusal == "candidate changed nothing"
    assert receipt.child_exit == 0


def test_a_failed_child_that_wrote_something_is_still_judged(repo: Path) -> None:
    """Failure plus work is not the same as failure plus nothing.

    A child killed at its wall clock, or one that errored after editing,
    may still have written a correct change. Discarding it unread throws
    away a candidate the declared validation could have judged.
    """

    def failed_but_wrote(worktree: Path) -> ProcessResult:
        (worktree / "src" / "app.py").write_text("VALUE = 2\n")
        return ProcessResult(1, "", "cut off", timed_out=True)

    receipt = deliver(
        repo, "partial", "p", failed_but_wrote, VALIDATION, writable=("src/**",)
    )
    assert receipt.outcome == "candidate-created"
    assert receipt.child_exit == 1
    assert receipt.child_timed_out is True
    assert receipt.validation_exit == 0


def test_the_receipt_carries_the_child_exit_on_every_path(repo: Path) -> None:
    """A field recorded on only some branches is one a reader cannot trust."""
    outcomes = {
        "ok": deliver(
            repo, "a", "p", _writer("VALUE = 2\n"), VALIDATION, writable=("src/**",)
        ),
        "bad-validation": deliver(
            repo, "b", "p", _writer("VALUE = 9\n"), VALIDATION, writable=("src/**",)
        ),
        "out-of-scope": deliver(
            repo,
            "c",
            "p",
            _writer("x = 1\n", path="stray.py"),
            VALIDATION,
            writable=("src/**",),
        ),
    }
    for name, receipt in outcomes.items():
        assert receipt.payload()["child_exit"] == 0, name


def test_a_dirty_repository_is_refused_not_stashed(repo: Path) -> None:
    """Rule 6: partial snapshots are forbidden and complete ones are deferred.

    Refusing is the only safe answer -- the alternative is a candidate
    whose base is not any commit that exists.
    """
    (repo / "src" / "app.py").write_text("VALUE = 7\n")
    with pytest.raises(DeliveryRefused, match="dirty repository"):
        deliver(
            repo, "x", "p", _writer("VALUE = 2\n"), VALIDATION, writable=("src/**",)
        )
    # The refusal did not touch the user's uncommitted work.
    assert (repo / "src" / "app.py").read_text() == "VALUE = 7\n"


def test_preflight_refuses_a_non_repository(tmp_path: Path) -> None:
    with pytest.raises(DeliveryRefused, match="not a git repository"):
        preflight(tmp_path)


def test_a_crashing_model_call_still_cleans_up(repo: Path) -> None:
    """Infrastructure failure must not leave a worktree or branch behind."""

    def explode(worktree: Path) -> ProcessResult:
        raise RuntimeError("model process died")

    with pytest.raises(RuntimeError, match="model process died"):
        deliver(repo, "boom", "p", explode, VALIDATION, writable=("src/**",))

    assert _git(repo, "status", "--porcelain") == ""
    assert _git(repo, "branch", "--list", "satyrn/candidate/boom") == ""
    assert "satyrn-worktrees" not in _git(repo, "worktree", "list")


def test_delivery_is_repeatable_after_a_failure(repo: Path) -> None:
    """A stale branch or worktree from a prior run must not block the next.

    The first delivery leaves nothing, but this asserts the recovery path
    directly rather than trusting the previous test's cleanup.
    """
    deliver(
        repo, "same", "p", _writer("VALUE = 99\n"), VALIDATION, writable=("src/**",)
    )
    second = deliver(
        repo, "same", "p", _writer("VALUE = 2\n"), VALIDATION, writable=("src/**",)
    )
    assert second.outcome == "candidate-created"


def test_the_receipt_records_the_conditions(repo: Path) -> None:
    receipt = deliver(
        repo,
        "recorded",
        "make VALUE 2",
        _writer("VALUE = 2\n"),
        VALIDATION,
        writable=("src/**",),
        cell={"model": "test/model", "tools": "read,write"},
    )
    payload = receipt.payload()
    assert payload["cell"] == {"model": "test/model", "tools": "read,write"}
    assert payload["prompt_sha256"] and len(str(payload["prompt_sha256"])) == 64
    assert payload["validation_command"] == list(VALIDATION)
    assert payload["base_sha"] == _git(repo, "rev-parse", "HEAD")
    assert "candidate" in str(payload["outcome"])
    # No outcome in this cycle is named `promoted` -- rule 5.
    assert payload["outcome"] != "promoted"
