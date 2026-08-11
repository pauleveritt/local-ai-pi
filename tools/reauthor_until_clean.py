"""Get a task's contract clean, or record exactly why it isn't.

A design review of tonight's plan found the shape of bug this project keeps
finding the hard way: the obvious implementation destroys evidence.
`author_contract.py` writes to fixed paths and deletes on rejection --
correct for one attended authoring call, wrong for an unattended loop that
retries into the same directory, where attempt 2 silently erases attempt 1
and a rejected retry deletes a previously-*accepted* draft.

So every attempt here writes into its own fresh directory under `--work-dir`
and nothing is lost. The task's file in `--out` only ever changes when a
strictly better result is found -- a clean draft replacing a leaking one, or
a first draft where there was none. A task that never cleans up leaves
`--out` exactly as it found it, plus a manifest entry saying why.

`autowire` on disk right now has a draft and no probe result -- "missing"
must mean "probe what exists" (~7 minutes), not "discard and re-author"
(~10-30 minutes for a worse expected outcome, since the existing draft is
already-written work). This orders every task through: reuse if clean,
probe-then-reuse if unmeasured, re-author only what's confirmed leaking.
"""

import argparse
import json
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from harness.reconstruction import Reconstruction, contract_hash


class Budget:
    """Shared stop conditions, checked before every model-calling unit of work.

    Two independent reasons to stop: time, and a dead server. Either one
    checked only between tasks would let a single task's retry loop burn
    the whole remaining budget or spend attempts against infrastructure
    that cannot answer -- both observed tonight in different tools.
    """

    def __init__(self, max_seconds: float, max_consecutive_infra_failures: int):
        self._deadline = time.monotonic() + max_seconds
        self._max_streak = max_consecutive_infra_failures
        self._streak = 0
        self.infra_aborted = False

    def expired(self) -> bool:
        return time.monotonic() >= self._deadline

    def record(self, produced_output: bool) -> None:
        """Record one model-calling attempt's shape, not its verdict.

        `produced_output` means the child wrote *something* -- a raw
        transcript, a reply -- not that the result was good. A model that
        tried and was correctly judged leaking is not an infrastructure
        failure; a child that produced nothing at all, repeatedly, is the
        dead-server shape.
        """
        if produced_output:
            self._streak = 0
            return
        self._streak += 1
        if self._streak >= self._max_streak:
            self.infra_aborted = True


@dataclass(frozen=True)
class AuthorResult:
    produced_draft: bool
    draft_path: Path | None


@dataclass(frozen=True)
class TaskOutcome:
    task_id: str
    status: str  # already-clean | reused-existing | cleaned-after-N | still-leaking | infra-aborted | deadline
    attempts: int = 0
    leaked: tuple[str, ...] = ()


def classify(task_id: str, drafts_dir: Path, probe_dir: Path) -> str:
    """One of: clean, needs-probe, needs-authoring.

    `needs-probe` covers both "never probed" and "probed, but the hash on
    file doesn't match the current draft" -- in both cases the right next
    step is to measure what's actually on disk, not to assume either
    verdict about it.
    """
    draft = drafts_dir / f"{task_id}.md"
    if not draft.is_file():
        return "needs-authoring"
    result = probe_dir / f"{task_id}.json"
    if not result.is_file():
        return "needs-probe"
    payload = json.loads(result.read_text())
    if contract_hash(draft.read_text()) != payload.get("contract_sha256"):
        return "needs-probe"
    if payload.get("leaked"):
        return "needs-authoring"
    return "clean"


def _promote(task_id: str, draft: Path, result: Reconstruction, out_dir: Path, probe_out: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    probe_out.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{task_id}.md").write_text(draft.read_text())
    (probe_out / f"{task_id}.json").write_text(
        json.dumps(result.payload(), indent=2, sort_keys=True) + "\n"
    )


def ready_task(
    task_id: str,
    drafts_dir: Path,
    probe_dir: Path,
    work_dir: Path,
    out_dir: Path,
    author: Callable[[Path], AuthorResult],
    probe: Callable[[Path], Reconstruction],
    budget: Budget,
    max_attempts: int,
) -> TaskOutcome:
    """Get one task admitted, or record why it can't be tonight.

    `author` and `probe` are injected so the state machine -- reuse,
    probe-first, bounded retry, promote-on-clean-only -- is tested without
    a model or a subprocess. Wired to real subprocess calls in `main`.
    """
    state = classify(task_id, drafts_dir, probe_dir)

    if state == "clean":
        return TaskOutcome(task_id, "already-clean")

    if state == "needs-probe":
        draft = drafts_dir / f"{task_id}.md"
        result = probe(draft)
        if not result.leaked:
            _promote(task_id, draft, result, out_dir, probe_dir)
            return TaskOutcome(task_id, "reused-existing")
        # Confirmed leaking now -- record it so a re-run doesn't re-probe.
        probe_dir.mkdir(parents=True, exist_ok=True)
        (probe_dir / f"{task_id}.json").write_text(
            json.dumps(result.payload(), indent=2, sort_keys=True) + "\n"
        )
        state = "needs-authoring"

    if state != "needs-authoring":
        raise AssertionError(f"unreachable classification: {state}")

    last_leaked: tuple[str, ...] = ()
    for attempt in range(1, max_attempts + 1):
        if budget.expired():
            return TaskOutcome(task_id, "deadline", attempt - 1, last_leaked)
        attempt_dir = work_dir / task_id / f"attempt{attempt}"
        result_a = author(attempt_dir)
        budget.record(result_a.produced_draft)
        if budget.infra_aborted:
            return TaskOutcome(task_id, "infra-aborted", attempt, last_leaked)
        if not result_a.produced_draft:
            continue
        if budget.expired():
            return TaskOutcome(task_id, "deadline", attempt, last_leaked)
        assert result_a.draft_path is not None
        recon = probe(result_a.draft_path)
        budget.record(True)
        if not recon.leaked:
            _promote(task_id, result_a.draft_path, recon, out_dir, probe_dir)
            return TaskOutcome(task_id, "cleaned-after-N", attempt)
        last_leaked = recon.leaked

    return TaskOutcome(task_id, "still-leaking", max_attempts, last_leaked)


def _subprocess_author(
    task_id: str, model: str, server: str, prompt: Path, timeout: float
) -> Callable[[Path], AuthorResult]:
    def run(attempt_dir: Path) -> AuthorResult:
        attempt_dir.mkdir(parents=True, exist_ok=True)
        code = subprocess.run(
            [
                sys.executable, "-m", "tools.author_contract",
                "--task", task_id, "--model", model, "--server", server,
                "--prompt", str(prompt), "--out", str(attempt_dir),
                "--timeout", str(timeout),
            ],
            capture_output=True, text=True,
        ).returncode
        draft = attempt_dir / f"{task_id}.md"
        # `code == 0` is the gate's opinion (length/timeout/budget); a raw
        # transcript existing is the infrastructure signal `Budget` needs,
        # and the two are deliberately checked separately -- a rejected
        # draft still proves the server answered.
        raw = attempt_dir / f"{task_id}.raw.md"
        produced_anything = raw.is_file() and raw.stat().st_size > 0
        return AuthorResult(
            produced_draft=(code == 0 and draft.is_file()), draft_path=draft if code == 0 else None
        ) if produced_anything else AuthorResult(False, None)

    return run


def _subprocess_probe(
    task_id: str, model: str, server: str, references: Path, cohort: Path, probe_scratch: Path
) -> Callable[[Path], Reconstruction]:
    def run(draft: Path) -> Reconstruction:
        scratch = probe_scratch / f"{task_id}-{contract_hash(draft.read_text())[:8]}"
        subprocess.run(
            [
                sys.executable, "-m", "tools.leak_probe",
                "--cohort", str(cohort), "--model", model, "--server", server,
                "--contract-dir", str(draft.parent), "--references", str(references),
                "--task", task_id, "--out", str(scratch),
            ],
            capture_output=True, text=True,
        )
        payload = json.loads((scratch / f"{task_id}.json").read_text())
        return Reconstruction(
            task_id=payload["task_id"],
            target=tuple(payload["target_signals"]),
            from_brief=tuple(payload["reconstructed_from_brief"]),
            from_contract=tuple(payload["reconstructed_from_contract"]),
            contract_sha256=payload["contract_sha256"],
        )

    return run


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", action="append", required=True)
    parser.add_argument("--author-model", required=True)
    parser.add_argument("--probe-model", required=True)
    parser.add_argument("--server", default="http://127.0.0.1:8001")
    parser.add_argument("--cohort", type=Path, default=Path("workloads/svcs/cohort.toml"))
    parser.add_argument(
        "--prompt", type=Path, default=Path("workloads/svcs/authoring-prompt.md")
    )
    parser.add_argument(
        "--references", type=Path, default=Path("workloads/svcs/reference-patches")
    )
    parser.add_argument("--drafts-dir", type=Path, required=True)
    parser.add_argument("--probe-dir", type=Path, default=None)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--author-timeout", type=float, default=900.0)
    parser.add_argument("--max-seconds", type=float, default=4 * 3600.0)
    parser.add_argument("--max-consecutive-infra-failures", type=int, default=3)
    args = parser.parse_args(argv)

    probe_dir = args.probe_dir or (args.drafts_dir / "probe")
    budget = Budget(args.max_seconds, args.max_consecutive_infra_failures)
    manifest: dict[str, dict[str, object]] = {}

    for task_id in args.task:
        outcome = ready_task(
            task_id,
            args.drafts_dir,
            probe_dir,
            args.work_dir,
            args.out,
            _subprocess_author(
                task_id, args.author_model, args.server, args.prompt, args.author_timeout
            ),
            _subprocess_probe(
                task_id, args.probe_model, args.server, args.references, args.cohort,
                args.work_dir / "_probes",
            ),
            budget,
            args.max_attempts,
        )
        manifest[task_id] = {
            "status": outcome.status,
            "attempts": outcome.attempts,
            "leaked": list(outcome.leaked),
        }
        print(
            f"{task_id:26} {outcome.status:18} attempts={outcome.attempts} "
            f"leaked={list(outcome.leaked)[:3]}",
            flush=True,
        )
        if outcome.status == "infra-aborted":
            print(
                f"\nABORTING: {args.max_consecutive_infra_failures} consecutive "
                "model calls produced no output. Server is likely down.",
                flush=True,
            )
            break
        if outcome.status == "deadline":
            print("\nSTOPPING: time budget exhausted.", flush=True)
            break

    args.work_dir.mkdir(parents=True, exist_ok=True)
    (args.work_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    clean = sum(1 for m in manifest.values() if m["status"] in ("already-clean", "reused-existing", "cleaned-after-N"))
    print(f"\n{clean}/{len(manifest)} tasks admitted (of {len(args.task)} requested)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
