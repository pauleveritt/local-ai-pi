"""The readiness loop's state machine, tested with a fake model and no subprocess.

`author` and `probe` are injected exactly so this can be verified without
spending a model call -- the property under test is the *sequencing*
(reuse before probing, probe before re-authoring, promote only on clean,
never touch `--out` on failure), and that sequencing is what a design
review found broken in the naive version of this loop: overwritten
drafts, a rejected retry deleting a previously-accepted one, and
`autowire`'s unmeasured draft being discarded instead of probed first.
"""

import json
from pathlib import Path

import pytest

from harness.reconstruction import Reconstruction, contract_hash
from tools.reauthor_until_clean import (
    AuthorResult,
    Budget,
    classify,
    ready_task,
)


def _recon(task_id: str, contract: str, leaked: tuple) -> Reconstruction:
    target = ("a", "b", "c", "d")
    from_contract = leaked + ("a",) if leaked else ("a",)
    return Reconstruction(
        task_id=task_id,
        target=target,
        from_brief=("a",),
        from_contract=from_contract,
        contract_sha256=contract_hash(contract),
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


# ---- classify --------------------------------------------------------


def test_classify_no_draft_needs_authoring(tmp_path: Path) -> None:
    assert classify("t", tmp_path / "d", tmp_path / "p") == "needs-authoring"


def test_classify_draft_no_probe_needs_probe(tmp_path: Path) -> None:
    drafts = tmp_path / "d"
    _write(drafts / "t.md", "x")
    assert classify("t", drafts, tmp_path / "p") == "needs-probe"


def test_classify_stale_probe_needs_probe_not_authoring(tmp_path: Path) -> None:
    """A hash mismatch means 're-measure what's here', not 'discard it'."""
    drafts, probes = tmp_path / "d", tmp_path / "p"
    _write(drafts / "t.md", "new bytes")
    _write(probes / "t.json", json.dumps({"leaked": [], "contract_sha256": "stale"}))
    assert classify("t", drafts, probes) == "needs-probe"


def test_classify_current_clean_probe_is_clean(tmp_path: Path) -> None:
    drafts, probes = tmp_path / "d", tmp_path / "p"
    _write(drafts / "t.md", "x")
    _write(
        probes / "t.json",
        json.dumps({"leaked": [], "contract_sha256": contract_hash("x")}),
    )
    assert classify("t", drafts, probes) == "clean"


def test_classify_current_leaking_probe_needs_authoring(tmp_path: Path) -> None:
    drafts, probes = tmp_path / "d", tmp_path / "p"
    _write(drafts / "t.md", "x")
    _write(
        probes / "t.json",
        json.dumps({"leaked": ["a.b"], "contract_sha256": contract_hash("x")}),
    )
    assert classify("t", drafts, probes) == "needs-authoring"


# ---- ready_task --------------------------------------------------------


def test_already_clean_task_spends_nothing(tmp_path: Path) -> None:
    drafts, probes, work, out = (tmp_path / n for n in ("d", "p", "w", "o"))
    _write(drafts / "t.md", "x")
    _write(probes / "t.json", json.dumps({"leaked": [], "contract_sha256": contract_hash("x")}))
    budget = Budget(max_seconds=999, max_consecutive_infra_failures=99)

    def author(_): raise AssertionError("must not author an already-clean task")
    def probe(_): raise AssertionError("must not re-probe an already-clean task")

    outcome = ready_task("t", drafts, probes, work, out, author, probe, budget, max_attempts=3)
    assert outcome.status == "already-clean"
    assert outcome.attempts == 0


def test_unmeasured_draft_is_probed_not_discarded(tmp_path: Path) -> None:
    """The autowire fix: a draft with no probe result is measured first."""
    drafts, probes, work, out = (tmp_path / n for n in ("d", "p", "w", "o"))
    _write(drafts / "t.md", "existing draft")
    budget = Budget(max_seconds=999, max_consecutive_infra_failures=99)

    def author(_): raise AssertionError("an unmeasured draft must be probed, not re-authored")
    def probe(draft):
        assert draft == drafts / "t.md"
        return _recon("t", draft.read_text(), leaked=())

    outcome = ready_task("t", drafts, probes, work, out, author, probe, budget, max_attempts=3)
    assert outcome.status == "reused-existing"
    assert (out / "t.md").read_text() == "existing draft"
    assert (probes / "t.json").is_file(), "the fresh probe result must be recorded"


def test_unmeasured_draft_that_turns_out_leaking_falls_through_to_authoring(tmp_path: Path) -> None:
    drafts, probes, work, out = (tmp_path / n for n in ("d", "p", "w", "o"))
    _write(drafts / "t.md", "leaks in prose")
    budget = Budget(max_seconds=999, max_consecutive_infra_failures=99)
    calls = {"authored": False}

    def probe(draft):
        if draft == drafts / "t.md":
            return _recon("t", draft.read_text(), leaked=("b",))
        return _recon("t", draft.read_text(), leaked=())

    def author(attempt_dir):
        calls["authored"] = True
        _write(attempt_dir / "t.md", "clean rewrite")
        return AuthorResult(True, attempt_dir / "t.md")

    outcome = ready_task("t", drafts, probes, work, out, author, probe, budget, max_attempts=3)
    assert calls["authored"], "a confirmed-leaking draft must trigger re-authoring"
    assert outcome.status == "cleaned-after-N"
    assert (out / "t.md").read_text() == "clean rewrite"


def test_a_leaking_task_that_cleans_up_on_attempt_two_stops_there(tmp_path: Path) -> None:
    drafts, probes, work, out = (tmp_path / n for n in ("d", "p", "w", "o"))
    _write(drafts / "t.md", "bad")
    _write(probes / "t.json", json.dumps({"leaked": ["x"], "contract_sha256": contract_hash("bad")}))
    budget = Budget(max_seconds=999, max_consecutive_infra_failures=99)
    attempts_made = []

    def author(attempt_dir):
        n = len(attempts_made) + 1
        attempts_made.append(n)
        _write(attempt_dir / "t.md", f"attempt {n}")
        return AuthorResult(True, attempt_dir / "t.md")

    def probe(draft):
        clean = draft.read_text() == "attempt 2"
        return _recon("t", draft.read_text(), leaked=() if clean else ("x",))

    outcome = ready_task("t", drafts, probes, work, out, author, probe, budget, max_attempts=3)
    assert outcome.status == "cleaned-after-N"
    assert outcome.attempts == 2
    assert len(attempts_made) == 2, "must stop at the first clean attempt, not run all 3"
    assert (out / "t.md").read_text() == "attempt 2"


def test_still_leaking_after_max_attempts_does_not_touch_out(tmp_path: Path) -> None:
    """The core promise: out only changes on a strictly better result."""
    drafts, probes, work, out = (tmp_path / n for n in ("d", "p", "w", "o"))
    _write(drafts / "t.md", "original leaking draft")
    _write(
        probes / "t.json",
        json.dumps({"leaked": ["x"], "contract_sha256": contract_hash("original leaking draft")}),
    )
    _write(out / "t.md", "original leaking draft")  # what a real prior run's --out holds
    budget = Budget(max_seconds=999, max_consecutive_infra_failures=99)

    def author(attempt_dir):
        _write(attempt_dir / "t.md", "still bad")
        return AuthorResult(True, attempt_dir / "t.md")

    def probe(draft):
        return _recon("t", draft.read_text(), leaked=("x",))

    outcome = ready_task("t", drafts, probes, work, out, author, probe, budget, max_attempts=3)
    assert outcome.status == "still-leaking"
    assert outcome.attempts == 3
    assert outcome.leaked == ("x",)
    assert (out / "t.md").read_text() == "original leaking draft", (
        "a task that never cleans up must leave --out exactly as it found it"
    )


def test_a_failed_authoring_attempt_still_counts_toward_max_attempts(tmp_path: Path) -> None:
    drafts, probes, work, out = (tmp_path / n for n in ("d", "p", "w", "o"))
    _write(drafts / "t.md", "bad")
    _write(probes / "t.json", json.dumps({"leaked": ["x"], "contract_sha256": contract_hash("bad")}))
    budget = Budget(max_seconds=999, max_consecutive_infra_failures=99)
    calls = {"n": 0}

    def author(attempt_dir):
        calls["n"] += 1
        # A budget-death or too-short attempt: no draft produced, but the
        # child DID answer (this is not the infra-failure shape).
        return AuthorResult(False, None)

    def probe(_): raise AssertionError("nothing to probe when authoring produced no draft")

    outcome = ready_task("t", drafts, probes, work, out, author, probe, budget, max_attempts=3)
    assert outcome.status == "still-leaking"
    assert calls["n"] == 3


# ---- Budget: deadline and infra-failure abort --------------------------


def test_budget_expired_stops_before_the_next_attempt(tmp_path: Path) -> None:
    drafts, probes, work, out = (tmp_path / n for n in ("d", "p", "w", "o"))
    _write(drafts / "t.md", "bad")
    _write(probes / "t.json", json.dumps({"leaked": ["x"], "contract_sha256": contract_hash("bad")}))
    budget = Budget(max_seconds=0, max_consecutive_infra_failures=99)  # already expired

    def author(_): raise AssertionError("must not spend an attempt once the deadline has passed")
    def probe(_): raise AssertionError("must not probe once the deadline has passed")

    outcome = ready_task("t", drafts, probes, work, out, author, probe, budget, max_attempts=3)
    assert outcome.status == "deadline"
    assert outcome.attempts == 0


def test_consecutive_infra_failures_abort_the_task(tmp_path: Path) -> None:
    """A dead server must stop the loop, not spend all max_attempts recording the same failure."""
    drafts, probes, work, out = (tmp_path / n for n in ("d", "p", "w", "o"))
    _write(drafts / "t.md", "bad")
    _write(probes / "t.json", json.dumps({"leaked": ["x"], "contract_sha256": contract_hash("bad")}))
    budget = Budget(max_seconds=999, max_consecutive_infra_failures=2)
    calls = {"n": 0}

    def author(_):
        calls["n"] += 1
        return AuthorResult(False, None)  # simulates a dead server: no reply at all

    def probe(_): raise AssertionError

    outcome = ready_task("t", drafts, probes, work, out, author, probe, budget, max_attempts=10)
    assert outcome.status == "infra-aborted"
    assert calls["n"] == 2, "must stop at the streak threshold, not run all 10 attempts"
    assert budget.infra_aborted


def test_a_successful_attempt_resets_the_infra_streak() -> None:
    budget = Budget(max_seconds=999, max_consecutive_infra_failures=2)
    budget.record(False)
    budget.record(True)  # a real reply -- even if the draft later fails the probe
    budget.record(False)
    assert not budget.infra_aborted, "the streak must reset on any produced output"
