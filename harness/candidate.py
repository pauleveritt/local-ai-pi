"""Turn one bounded model attempt into a durable candidate commit.

The product-shaped milestone this phase kept drifting past. Everything
before it measured models; this delivers something a contributor can
install and run against their own repository, and it is deliberately the
smallest thing that can do so.

**What it does not do**, from the roadmap's explicit exclusions: no
controller call, no repair call, no gate bundle, no symbol-loss check,
no copy into the live tree, no implicit fast-forward, no dirty-repository
snapshotting. Successful work becomes a durable ref the caller can
inspect, cherry-pick or delete. Nothing is promoted, and no outcome here
is named `promoted` -- governing rule 5.

**The live repository is never written to.** The model runs in a git
worktree created at HEAD; on failure the worktree and its branch are
removed and the live tree is untouched; on success the worktree is
removed and only a ref under `refs/satyrn/` survives. A dirty repository
is refused rather than stashed, because a partial snapshot is worse than
no snapshot and complete snapshotting is deferred -- governing rule 6.

The model call is injected rather than imported so the whole lifecycle
is testable without a model or a network, which is what keeps this
honest: every branch below is exercised by deterministic tests, and live
probes only confirm the integrated flow.
"""

import hashlib
import os
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from harness.processes import ProcessResult, run_process
from harness.workspace import GIT_ENV

CANDIDATE_NAMESPACE = "refs/satyrn/candidates"


class DeliveryRefused(Exception):
    """Preconditions were not met. Nothing was created and nothing ran."""


@dataclass(frozen=True)
class Receipt:
    """Everything a reader needs to judge one delivery without rerunning it."""

    repository: str
    base_sha: str
    outcome: str  # candidate-created | discarded | infrastructure-failure
    candidate_ref: str = ""
    candidate_commit: str = ""
    prompt_sha256: str = ""
    cell: dict[str, str] = field(default_factory=dict)
    changed_paths: tuple[str, ...] = ()
    out_of_scope: tuple[str, ...] = ()
    validation_command: tuple[str, ...] = ()
    validation_exit: int | None = None
    validation_timed_out: bool = False
    child_exit: int | None = None
    """The model child's exit status.

    Recorded on every path, because without it a contributor whose model
    server is unreachable reads `candidate changed nothing` -- a verdict
    on their model -- for what is a verdict on their setup. That was the
    first thing this tool said to anyone who had not already replicated
    the author's laptop.
    """
    child_timed_out: bool = False
    """Whether the model child was killed at its wall clock.

    Recorded rather than acted on: a truncated child may still have
    written usable work, and discarding it unread would throw away a
    candidate the validation could have judged.
    """
    validation_output_sha256: str = ""
    validation_tail: str = ""
    child_seconds: float = 0.0
    validation_seconds: float = 0.0
    commit_seconds: float = 0.0
    total_seconds: float = 0.0
    cleanup: str = ""
    refusal: str = ""

    def payload(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "base_sha": self.base_sha,
            "outcome": self.outcome,
            "candidate_ref": self.candidate_ref,
            "candidate_commit": self.candidate_commit,
            "prompt_sha256": self.prompt_sha256,
            "cell": dict(sorted(self.cell.items())),
            "changed_paths": list(self.changed_paths),
            "out_of_scope": list(self.out_of_scope),
            "validation_command": list(self.validation_command),
            "validation_exit": self.validation_exit,
            "validation_timed_out": self.validation_timed_out,
            "child_exit": self.child_exit,
            "child_timed_out": self.child_timed_out,
            "validation_output_sha256": self.validation_output_sha256,
            "validation_tail": self.validation_tail,
            "timings_seconds": {
                "child": round(self.child_seconds, 3),
                "validation": round(self.validation_seconds, 3),
                "commit": round(self.commit_seconds, 3),
                "total": round(self.total_seconds, 3),
            },
            "cleanup": self.cleanup,
            "refusal": self.refusal,
        }


def _git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, env=GIT_ENV
    )
    if check and result.returncode != 0:
        raise DeliveryRefused(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def preflight(repo: Path) -> str:
    """Refuse anything but a clean repository, and return its HEAD.

    A dirty tree is refused rather than stashed. Complete dirty-state
    snapshotting is deferred and partial snapshots are forbidden, so the
    only safe answer is to decline: the alternative is a candidate whose
    base is not any commit that exists.
    """
    if not (repo / ".git").exists():
        raise DeliveryRefused(f"{repo} is not a git repository")
    dirty = _git(repo, "status", "--porcelain")
    if dirty:
        raise DeliveryRefused(
            "refusing to deliver into a dirty repository:\n"
            + "\n".join(f"  {line}" for line in dirty.splitlines()[:10])
            + "\n\nCommit or stash first. Partial snapshots are forbidden and "
            "complete ones are not implemented, so this refuses rather than "
            "guessing which of your changes to preserve."
        )
    return _git(repo, "rev-parse", "HEAD")


def _out_of_scope(
    changed: tuple[str, ...], writable: tuple[str, ...]
) -> tuple[str, ...]:
    import fnmatch

    if not writable:
        return ()
    return tuple(
        path
        for path in changed
        if not any(fnmatch.fnmatch(path, pattern) for pattern in writable)
    )


def model_server_reachable(base_url: str, timeout: float = 10.0) -> bool:
    """Is the model server answering *now*, just after a child timed out?

    The one question that separates "your server is down" from "the model
    burned its whole budget and wrote nothing". Both leave an empty tree
    and a non-zero exit, which is why `deliver()` could not tell them
    apart and called every timeout an infrastructure failure.

    Deliberately conservative: an unknown or unparseable `base_url`, and
    any error at all, answer `False` -- which preserves the old
    infrastructure-failure classification. This may only ever *reclassify
    a timeout as a model failure*, never the reverse, so a genuinely dead
    server can never be blamed on the model.

    A liveness check after the fact is not proof the server was up for the
    whole attempt; it is evidence, and the refusal text says so.
    """
    if not base_url or base_url == "?":
        return False
    try:
        import urllib.request

        with urllib.request.urlopen(
            base_url.rstrip("/") + "/models", timeout=timeout
        ) as response:
            return 200 <= response.status < 300
    except Exception:  # noqa: BLE001 -- any failure means "cannot confirm alive"
        return False


def deliver(
    repo: Path,
    task_id: str,
    prompt: str,
    run_model: Callable[[Path], ProcessResult],
    validation: tuple[str, ...],
    *,
    writable: tuple[str, ...] = (),
    cell: dict[str, str] | None = None,
    validation_timeout: float = 900.0,
    validation_env: dict[str, str] | None = None,
    server_probe: Callable[[], bool] | None = None,
) -> Receipt:
    """One attempt, delivered as a candidate ref or discarded cleanly."""
    started = time.monotonic()
    base_sha = preflight(repo)
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    branch = f"satyrn/candidate/{task_id}"
    worktree = repo / ".git" / "satyrn-worktrees" / task_id

    def receipt(outcome: str, **kwargs: object) -> Receipt:
        return Receipt(
            repository=str(repo),
            base_sha=base_sha,
            outcome=outcome,
            prompt_sha256=prompt_hash,
            cell=dict(cell or {}),
            validation_command=validation,
            total_seconds=time.monotonic() - started,
            **kwargs,  # type: ignore[arg-type]
        )

    _git(repo, "worktree", "prune")
    _git(repo, "branch", "-D", branch, check=False)
    _git(repo, "worktree", "add", "-q", "-b", branch, str(worktree), base_sha)

    cleanup = "worktree removed"
    try:
        child_started = time.monotonic()
        child = run_model(worktree)
        child_seconds = time.monotonic() - child_started

        # Two explicit queries rather than parsing `status --porcelain`.
        # Porcelain's status field is two characters plus a space, and the
        # helper above strips the output -- which ate the leading space of
        # the first line and turned `src/app.py` into `rc/app.py`. A fixed
        # offset into a stripped string is a silent scope bug, and it
        # rejected a correct candidate before any test caught it.
        tracked = _git(worktree, "diff", "--name-only", "HEAD").splitlines()
        untracked = _git(
            worktree, "ls-files", "--others", "--exclude-standard"
        ).splitlines()
        changed = tuple(sorted({*tracked, *untracked}))
        outside = _out_of_scope(changed, writable)
        if not changed and (child.returncode != 0 or child.timed_out):
            # A child that failed and left nothing is a broken setup, not a
            # model that declined. Checked before `changed nothing` because
            # the two are indistinguishable from the tree alone, and the
            # wrong one of the pair blames the reader's model for their
            # unreachable server. A child that failed but *did* write is
            # left to validation: truncated work can still be correct, and
            # discarding it unread throws away a judgeable candidate.
            #
            # ...except for one case the tree genuinely cannot show, and
            # which cost a batch on 2026-08-15: a model that spends its
            # whole wall clock without writing. That also arrives here as
            # "timed out, nothing on disk", was called an infrastructure
            # failure, and the batch driver voids and *retries* an
            # infrastructure failure -- three 900s attempts per slot,
            # ending in `void_exhausted` with no data and a receipt
            # blaming a server that was up the whole time. The Cycle 7
            # pre-registration is explicit that exhausting the budget is a
            # plain failure ("candidate-created = false"), not a void, so
            # the misclassification silently corrupts denominators.
            #
            # The discriminator is one question the tree cannot answer:
            # is the server answering? Asked only on a timeout, and only
            # able to turn infra into a recorded failure, never the
            # reverse (see `model_server_reachable`).
            probe = server_probe or (
                lambda: model_server_reachable((cell or {}).get("base_url", ""))
            )
            if child.timed_out and probe():
                return receipt(
                    "discarded",
                    child_seconds=child_seconds,
                    child_exit=child.returncode,
                    child_timed_out=child.timed_out,
                    cleanup=cleanup,
                    refusal=(
                        "the model exhausted its time budget without writing "
                        "anything. The model server answered a liveness check "
                        "immediately afterwards, so this is recorded as a "
                        "model failure rather than a broken setup. (A check "
                        "after the fact cannot prove the server was up for the "
                        "whole attempt -- it is evidence, not a guarantee.)"
                    ),
                )
            return receipt(
                "infrastructure-failure",
                child_seconds=child_seconds,
                child_exit=child.returncode,
                child_timed_out=child.timed_out,
                cleanup=cleanup,
                refusal=(
                    f"the model call failed (exit {child.returncode}"
                    f"{', timed out' if child.timed_out else ''}) and wrote "
                    "nothing. This is a problem with the setup, not with the "
                    "candidate: check that the model server is running and "
                    "that the model name resolves."
                ),
            )
        if outside:
            # Discarded before validation on purpose: running a declared
            # validation over a candidate that wrote outside its bounds
            # would report on work nobody asked for.
            return receipt(
                "discarded",
                changed_paths=changed,
                out_of_scope=outside,
                child_seconds=child_seconds,
                child_exit=child.returncode,
                child_timed_out=child.timed_out,
                cleanup=cleanup,
                refusal="candidate wrote outside the writable policy",
            )
        if not changed:
            return receipt(
                "discarded",
                child_seconds=child_seconds,
                child_exit=child.returncode,
                child_timed_out=child.timed_out,
                cleanup=cleanup,
                refusal="candidate changed nothing",
            )

        validation_started = time.monotonic()
        # The caller's environment, not GIT_ENV. GIT_ENV pins PATH to
        # `os.defpath` for git determinism, which is correct for git and
        # wrong for anything else -- a validation command found on the
        # user's PATH would vanish, and the failure reads as a broken
        # candidate rather than a broken harness.
        checked = run_process(
            validation,
            cwd=worktree,
            timeout=validation_timeout,
            env=validation_env or dict(os.environ),
        )
        validation_seconds = time.monotonic() - validation_started
        output = (checked.stdout or "") + (checked.stderr or "")
        common = dict(
            changed_paths=changed,
            child_exit=child.returncode,
            child_timed_out=child.timed_out,
            child_seconds=child_seconds,
            validation_seconds=validation_seconds,
            validation_exit=checked.returncode,
            validation_timed_out=checked.timed_out,
            validation_output_sha256=hashlib.sha256(output.encode()).hexdigest(),
            validation_tail=output[-2000:],
        )
        if checked.returncode != 0 or checked.timed_out:
            return receipt(
                "discarded",
                cleanup=cleanup,
                refusal="declared validation did not pass",
                **common,
            )

        commit_started = time.monotonic()
        _git(worktree, "add", "-A")
        _git(
            worktree,
            "-c",
            "user.name=satyrn-engine",
            "-c",
            "user.email=satyrn-engine@localhost",
            "commit",
            "-q",
            "--no-gpg-sign",
            "-m",
            f"candidate: {task_id}\n\nbase: {base_sha}\nprompt: {prompt_hash}",
        )
        candidate_commit = _git(worktree, "rev-parse", "HEAD")
        ref = f"{CANDIDATE_NAMESPACE}/{task_id}"
        # A ref rather than a branch: durable, inspectable, and out of the
        # way of `git branch`. The caller accepts or deletes it; nothing
        # here merges or fast-forwards anything.
        _git(repo, "update-ref", ref, candidate_commit)
        commit_seconds = time.monotonic() - commit_started

        return receipt(
            "candidate-created",
            candidate_ref=ref,
            candidate_commit=candidate_commit,
            commit_seconds=commit_seconds,
            cleanup=cleanup,
            **common,
        )
    finally:
        # The worktree goes whatever happened; the ref, if one was made,
        # survives. `--force` because the tree is dirty by construction on
        # the discard paths.
        _git(repo, "worktree", "remove", "--force", str(worktree), check=False)
        _git(repo, "branch", "-D", branch, check=False)
        _git(repo, "worktree", "prune", check=False)
