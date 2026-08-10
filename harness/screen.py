"""One bounded model attempt per replay task, graded by its hidden oracle.

This is the *screen*, and its job is narrow: find out whether the frozen
cohort spreads outcomes. It is explicitly not evidence. It runs one
attempt per task with no repetition, no interleaving, and no
pre-registered margins, so nothing it produces may be pooled into a
later confirmatory result.

What it does establish is the thing qualification cannot: qualification
proves each task is *well-formed* -- base green, oracle rejects the base
for a declared reason, target green. It says nothing about whether a
small local model lands anywhere other than all-pass or all-fail. A
cohort that is entirely floor or entirely ceiling is AgentClinic Phase 2
rebuilt with more ceremony, and one screening pass is the cheapest way
to find that out before anything is built on top.

**The arm is brief-only.** The executor sees the task's `brief.md` and
the base tree, nothing else -- no contract, because contracts are not
authored yet. In the roadmap's terms this is the concise-brief arm, not
the complete-contract arm, and results must be reported under that name.
"""

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from harness.processes import run_process
from harness.runner import _pi_command, pi_env
from harness.similarity import overlap
from harness.validity import VALID, assess
from harness.workload import (
    CohortEnv,
    Manifest,
    SuiteResult,
    WorkloadError,
    materialize,
    overlay_oracle,
    run_suite,
    sha256_file,
)
from harness.workspace import GIT_ENV

# The envelope, matching Phase 7-pre's `envelope-cap.ts` exactly: one
# call, read and write only, 16 turns, 30 tool calls. The budgets live in
# the extension; the tool allowlist has to be passed on the command line.
# Phase 7-pre's envelope. Kept as the default so the historical arm is
# reproducible by name, but it is now known not to transfer: Pi's built-in
# tools are read, bash, edit, write, and without `bash` there is no way to
# enumerate a repository. On AgentClinic Phase 2 -- three files, named in
# the spec -- that never mattered.
ENVELOPE_TOOLS = "read,write"
ENVELOPE_EXTENSION = (
    Path(__file__).resolve().parents[1] / "extensions" / "envelope-cap.ts"
)
PROBE_EXTENSION = Path(__file__).resolve().parents[1] / "extensions" / "probe-cap.ts"
"""Loose budgets for a headroom probe, which is not the same thing as an arm.

The envelope's 16 turns and 30 tool calls mirror the engine's implementer
child and were calibrated for `read,write` with no way to execute anything.
Once the executor has a working environment it has more useful work to do
per task, and the budget did not move with it: on `registry-iter` -- the
declared floor -- the model closed the whole gap, ran the suite, found a
doctest it had just broken, and hit the ceiling before it could repair it.
A probe whose budget truncates repair manufactures the false floor it exists
to rule out.
"""


@dataclass(frozen=True)
class Attempt:
    """One model attempt against one task, with its grading.

    `oracle_delta` is the experimental signal; `accepted` is the product
    gate. Keeping both is deliberate: acceptance is binary and throws
    away nearly everything, while a delta of zero against a base that
    already scores 15/18 is the difference between "nearly there" and
    "did nothing" -- a distinction this project got wrong once already.
    """

    task_id: str
    manifest_sha256: str
    rule_version: int
    tools: str
    accepted: bool
    outcome: str
    base_passed: int
    target_total: int
    oracle_delta: int
    gap_closed: float
    missing_nodes: tuple[str, ...]
    oracle_shortfall: tuple[str, ...]
    changed_paths: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    model_seconds: float
    model_timed_out: bool
    preservation: SuiteResult | None
    oracle: SuiteResult | None
    argv: tuple[str, ...] = field(default=(), repr=False)
    prompt_sha256: str = ""
    """Hash of the exact prompt bytes the executor was given.

    The arm is no longer "the brief" once anything is composed onto it,
    and a record that names the arm but not the bytes cannot prove two
    attempts were given the same thing. Governing rule 3 already lists
    prompt bytes as a recorded condition; nothing was recording them.
    """
    reference_overlap: float = -1.0
    """Share of added production lines found verbatim in the target diff.

    -1 when no reference patch was available to compare against, which
    is not the same as 0 and must not be averaged with it.

    Recorded, never used to reject. It flagged the copied `autowire`
    candidate at 100% before anyone read a transcript, but a high score
    is a reason to read the candidate, not a verdict: `flask-extensions`
    scores 100% from both models on a six-line change the brief all but
    dictates.
    """
    validity: str = VALID
    """Whether this is a result at all: "valid", or "void:<reason>".

    Decided from the transcript before grading is consulted, because
    every outcome the acceptance rule can express assumes the model
    wrote the candidate -- and Cycle 1 produced one that read the target
    implementation and the hidden oracle out of a leftover workspace,
    then deleted the traces. That grade was accurate and meaningless.
    """
    validity_evidence: tuple[str, ...] = ()
    model_timeout_seconds: float = 0.0
    """The wall-clock cap the attempt ran under.

    An arm condition, and it was missing while `model_timed_out` was
    present -- so a truncated attempt recorded that it was truncated but
    not what truncated it, and two runs under different caps were
    indistinguishable afterwards. The same oversight as inheriting the
    turn envelope: budgets were raised fourfold and the wall clock left
    at a number chosen for a different arm.
    """
    wrote_tests: tuple[str, ...] = ()
    """Test files the model wrote, permitted and never executed.

    Its own field rather than folded into `out_of_scope`, because it is
    the finding of a different question: no brief tells the model not to
    write tests, writing one is ordinary practice, and every target
    commit in this cohort does it. If contracts have to carry "do not
    write tests" to keep candidates in scope, that instruction is a real
    cost of the pre-chewed-work pitch and its rate is what says so.
    """
    budget_exhausted: str = "none"
    """Which budget ran out: "none", "turns", "tools", or "turns+tools".

    Lifted out of the transcript rather than inferred. A run that stopped
    because it ran out of budget is not a run that could not do the work,
    and without this the two are the same record -- the extension writes
    the distinction into the transcript and nothing was carrying it into
    the result.
    """
    cell: dict[str, str] = field(default_factory=dict)
    """The resolved experimental cell: what this attempt actually ran under.

    Governing rule 3 requires prompt bytes, model, tools, budgets and
    environment to be condition-recorded. That was honoured in prose and
    not in code: Experiment B's 32768 output cap existed only in its
    driver and its directory name, so a record moved out of that
    directory could not say what it ran under. Resolved at call time
    rather than declared, because a declared value is the one that drifts.
    """
    executor_env_lock_sha256: str = "none"
    """Which environment the *executor* had, or "none" for a bare tree.

    An arm condition, not a grading one, so it does not bump
    `GRADING_RULE_VERSION` -- but it changes what a result means as much
    as the tool list does, and two attempts recorded without it are not
    comparable. A model that can run the base suite is doing a different
    task from one that cannot.
    """

    @property
    def summary(self) -> str:
        """The line a human reads, which must never hide the control."""
        candidate = self.oracle.tests_passed if self.oracle else 0
        return (
            f"candidate {candidate}/{self.target_total}; base {self.base_passed}; "
            f"delta {self.oracle_delta:+d}; gap closed {self.gap_closed:.0%}"
        )

    def payload(self) -> dict[str, object]:
        def suite(result: SuiteResult | None) -> dict[str, object] | None:
            if result is None:
                return None
            return {
                "reason_class": result.reason_class,
                "tests_passed": result.tests_passed,
                "node_count": len(result.outcomes),
                "failures": dict(sorted(result.failures.items())),
                "collection_errors": dict(sorted(result.collection_errors.items())),
                "wall_seconds": round(result.wall_seconds, 3),
            }

        return {
            "task_id": self.task_id,
            "manifest_sha256": self.manifest_sha256,
            "rule_version": self.rule_version,
            "tools": self.tools,
            "accepted": self.accepted,
            "outcome": self.outcome,
            "base_passed": self.base_passed,
            "target_total": self.target_total,
            "oracle_delta": self.oracle_delta,
            "gap_closed": self.gap_closed,
            "missing_nodes": list(self.missing_nodes),
            "oracle_shortfall": list(self.oracle_shortfall),
            "changed_paths": list(self.changed_paths),
            "out_of_scope": list(self.out_of_scope),
            "model_seconds": round(self.model_seconds, 2),
            "model_timed_out": self.model_timed_out,
            "preservation": suite(self.preservation),
            "oracle": suite(self.oracle),
            "argv": list(self.argv),
            "prompt_sha256": self.prompt_sha256,
            "reference_overlap": self.reference_overlap,
            "validity": self.validity,
            "validity_evidence": list(self.validity_evidence),
            "model_timeout_seconds": self.model_timeout_seconds,
            "wrote_tests": list(self.wrote_tests),
            "budget_exhausted": self.budget_exhausted,
            "cell": dict(sorted(self.cell.items())),
            "executor_env_lock_sha256": self.executor_env_lock_sha256,
        }


GUARD_EXTENSION = Path(__file__).resolve().parents[1] / ".pi" / "extensions" / "loop-breaker.ts"
"""The shipped loop breaker, the one contributors install.

Adding it changes the extension set, which makes a guarded run a
different cell from an unguarded one -- not the same arm with a helper.
Replay shows it fires on both of this phase's recorded retry loops and
on neither of two accepted runs from the same cells; whether the model
then does something *else* is what only a live run can answer.
"""


def resolve_cell(
    model: str, tools: str, extensions: tuple[Path, ...], timeout: float
) -> dict[str, str]:
    """Everything about this attempt that a later reader must not have to infer.

    Resolved by reading the actual configuration -- the model entry Pi
    will use, the extension bytes, the installed Pi version -- rather
    than by restating the flags. A restated flag agrees with the run by
    convention; a hash of the file disagrees loudly when someone edits
    it mid-sweep, which is exactly what happened when an output cap was
    swapped for one stage and restored afterwards.
    """
    # Order-sensitive on purpose: extensions load in sequence, and two
    # sets with the same members in a different order are not the same
    # arm.
    digests = ":".join(
        sha256_file(e) if e.is_file() else "absent" for e in extensions
    )
    cell: dict[str, str] = {
        "model": model,
        "tools": tools,
        "extensions": ",".join(e.name for e in extensions),
        "extensions_sha256": hashlib.sha256(digests.encode()).hexdigest(),
        "wall_clock_seconds": str(timeout),
    }
    try:
        version = subprocess.run(
            ["pi", "--version"], capture_output=True, text=True, timeout=30
        )
        cell["pi_version"] = version.stdout.strip() or version.stderr.strip()
    except Exception:
        cell["pi_version"] = "unknown"

    models_json = Path(pi_env(inherit_venv=True).get("PI_CODING_AGENT_DIR", "")) / "models.json"
    cell["models_json_sha256"] = (
        sha256_file(models_json) if models_json.is_file() else "absent"
    )
    # The resolved per-model limits, not the flag: `maxTokens` is the
    # value that silently made four of gemma's five failures look like
    # incapacity, and it appeared in no attempt record.
    if models_json.is_file():
        data = json.loads(models_json.read_text())
        wanted = model.split("/", 1)[-1]
        for provider in data.get("providers", {}).values():
            for entry in provider.get("models", []):
                if entry.get("id") == wanted:
                    cell["max_tokens"] = str(entry.get("maxTokens", "?"))
                    cell["context_window"] = str(entry.get("contextWindow", "?"))
                    cell["base_url"] = str(provider.get("baseUrl", "?"))
    return cell


def budget_exhaustion(transcript: str) -> str:
    """Which budgets the cap extension reported exhausted, if any.

    Read from the transcript rather than reconstructed by counting turns
    here, because the extension is the thing that actually enforces the
    cap and a second implementation of the same arithmetic would be free
    to disagree with it.
    """
    hit = [
        name
        for name, marker in (
            ("turns", "turn_budget_exhausted"),
            ("tools", "tool_budget_exhausted"),
        )
        if marker in transcript
    ]
    return "+".join(hit) if hit else "none"


def provision_executor_env(workspace: Path, env_source: Path) -> str:
    """Give the executor a working dev environment, and return its lock hash.

    The phase claims a small model can do *routine, pre-chewed coding
    work*. Routine work happens in a repository that has a working
    environment; an executor that cannot run anything is being asked to
    write correct code blind, which is a harder and more artificial task
    than the one being claimed. The screen measured the difference: a
    model diagnosed `magicmock-factory` correctly and then spent turns 9
    through 16 failing to obtain a runnable Python, exhausted its turn
    budget, and graded `no-changes`.

    Same lock as the grading environment, dependencies only. `svcs`
    itself is never installed -- `PYTHONPATH` points at the workspace
    `src/`, exactly as `run_suite` does, so the executor imports the tree
    it is editing rather than a stale copy.

    Nothing new becomes reachable. Oracle files exist only inside the
    grading materializations, overlaid after the child has exited. The
    base tests the executor can now run are the ones already sitting in
    its workspace: they pass at base, contain no oracle nodes, and give
    regression signal, which is what a developer has. Editing them to
    cheat is already defeated -- `apply_candidate(include=writable)`
    strips test edits before both graded runs.

    The venv is git-excluded rather than gitignored, via `.git/info/exclude`,
    so the working tree stays byte-identical to base and `capture_candidate`
    never sweeps 60 MB of site-packages into the candidate patch.
    """
    venv = workspace / ".venv"
    exclude = workspace / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a") as handle:
        handle.write("\n/.venv/\n")

    environ = {**os.environ, "UV_PROJECT_ENVIRONMENT": str(venv)}
    result = subprocess.run(
        ["uv", "sync", "--locked", "--no-install-project", "-q"],
        cwd=env_source,
        capture_output=True,
        text=True,
        env=environ,
    )
    if result.returncode != 0:
        raise WorkloadError(f"executor env sync failed: {result.stderr.strip()}")
    if not (venv / "bin" / "python").is_file():
        raise WorkloadError(f"executor env has no interpreter at {venv}")
    return sha256_file(env_source / "uv.lock")


def executor_env_vars(workspace: Path) -> dict[str, str]:
    """Point the child's shell at the workspace venv and the workspace source."""
    venv = workspace / ".venv"
    env = pi_env()
    env["VIRTUAL_ENV"] = str(venv)
    env["PATH"] = os.pathsep.join([str(venv / "bin"), env.get("PATH", "")])
    # Mirrors `run_suite`. An editable install would be the obvious
    # alternative and is the wrong one: svcs versions itself with
    # hatch-vcs, and a materialized workspace is a synthetic single
    # commit with no tags for it to read.
    env["PYTHONPATH"] = str(workspace / "src")
    return env


def base_commit(workspace: Path) -> str:
    """The root commit `materialize` wrote. Everything is diffed against this."""
    result = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"],
        cwd=workspace,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    return result.stdout.strip().splitlines()[0]


def capture_candidate(workspace: Path) -> str:
    """The model's whole contribution, as a patch against the base commit.

    Diffed against the *root* commit rather than HEAD. The workspace is a
    real git repository and a model with a shell can commit in it; against
    HEAD, a committed change produces an empty diff and real work would be
    recorded as "no-changes" -- an inversion of exactly the kind this
    harness has already suffered three times.

    Saving the patch is what makes grading replayable. Every defect found
    here has been in the acceptance rule, never in the model's output, and
    each cost a fresh sweep to re-score work that was already correct.
    """
    subprocess.run(
        ["git", "add", "-A"], cwd=workspace, capture_output=True, env=GIT_ENV
    )
    diff = subprocess.run(
        ["git", "diff", "--cached", "--binary", base_commit(workspace)],
        cwd=workspace,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    return diff.stdout


def apply_candidate(
    workspace: Path, patch: str, include: tuple[str, ...] | None = None
) -> None:
    """Reapply a saved candidate, optionally restricted to certain paths.

    `include` is how grading stays honest about *what* it executes. Graded
    workspaces get production paths only, so a model-authored test,
    conftest, or pytest.ini is recorded as out-of-scope but never runs.
    Executing model-written test files would let a candidate grade itself.
    """
    if not patch.strip():
        return
    command = ["git", "apply", "--whitespace=nowarn"]
    for pattern in include or ():
        command.append(f"--include={pattern}")
    command.append("-")
    result = subprocess.run(
        command, cwd=workspace, input=patch, capture_output=True, text=True, env=GIT_ENV
    )
    if result.returncode != 0:
        raise WorkloadError(f"candidate patch did not apply: {result.stderr.strip()}")


def _changed_paths(workspace: Path) -> tuple[str, ...]:
    """Every path the model added, changed, or deleted.

    `git add -A` first: a model's new files start untracked, and a plain
    status would report them as a directory rather than by name.
    """
    subprocess.run(
        ["git", "add", "-A"], cwd=workspace, capture_output=True, env=GIT_ENV
    )
    listing = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=workspace,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    return tuple(sorted(p for p in listing.stdout.splitlines() if p.strip()))


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _out_of_scope(
    changed: tuple[str, ...],
    writable: tuple[str, ...],
    test_paths: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Changed paths that neither the writable policy nor the test roots admit.

    Three categories, not two. `writable` is what gets graded. `test_paths`
    is where the repository keeps its tests: writes there are permitted and
    recorded, never executed, and not an acceptance failure. Everything
    else -- changelog, prose docs, packaging, lockfiles -- is a violation.

    The middle category exists because all eight of this cohort's target
    commits write tests. Judging a candidate against `writable` alone
    rejected the reference answer on every task, which is the same defect
    that killed rule 4, arriving by a different route: the first executor
    to be given a shell and an environment wrote a test on both tasks it
    attempted, closed the whole oracle gap on both, and was rejected for
    doing what upstream did.

    Nothing about self-grading changes. `apply_candidate(include=writable)`
    still strips test edits before both graded runs, so a model-authored
    test is recorded and never runs.

    Recorded, not blocked: the screen observes what the model did; it does
    not constrain it.
    """
    return tuple(
        path
        for path in changed
        if not _matches(path, writable) and not _matches(path, test_paths)
    )


GRADING_RULE_VERSION = 8
"""Bumped whenever the acceptance rule changes.

Every grade records it, because eight rules have now produced different
verdicts on identical candidates and a record that does not say which one
scored it cannot be compared with anything.

  1  preservation on base tests, oracle on target tests -- contradictory
  2  both on the overlaid copy -- oracle counted twice
  3  overlay then --ignore -- a root conftest still loads as a plugin
  4  separate workspaces, production paths only, node inventory
  5  node inventory counts position-keyed nodes instead of naming them
  6  damage outranks scope violation in the reported outcome
  7  writing tests is permitted and recorded, not a scope violation
  8  every oracle node the target passed must pass here -- `pass` alone
     accepted a suite whose hidden assertions had been skipped

Rule 4 was found by the ceiling replay: the *target's own diff* graded as
`tests-vanished` on four of nine tasks, because Sybil node ids move when
production lines move. A rule that rejects the reference answer rejects
every correct answer.
"""


# svcs runs its README and its docstrings through Sybil, whose node ids
# are pure position: `path::line:N,column:M`. Adding or removing a single
# line above one renames every node below it, so comparing these by
# identity reports a *correct* candidate as having deleted tests. Twelve
# of them sit in `src/svcs/_core.py` and `README.md`, which is the file
# almost every task edits.
_POSITION_KEYED = re.compile(r"::line:\d+,column:\d+$")


def _node_census(nodes: Iterable[str]) -> tuple[set[str], dict[str, int]]:
    """Split node ids into stable identities and per-file position counts.

    Position-keyed nodes get counted per file rather than matched by
    name. Deleting a doctest still lowers the count and is caught;
    shifting one down four lines is not mistaken for deleting it.
    """
    stable: set[str] = set()
    counts: dict[str, int] = {}
    for node in nodes:
        if _POSITION_KEYED.search(node):
            path = node.split("::")[0]
            counts[path] = counts.get(path, 0) + 1
        else:
            stable.add(node)
    return stable, counts


def _vanished(
    expected_stable: set[str], expected_counts: dict[str, int], actual: Iterable[str]
) -> tuple[str, ...]:
    """Every base test the candidate made disappear, by either measure."""
    actual_stable, actual_counts = _node_census(actual)
    thinned = tuple(
        f"{path}::position-keyed {actual_counts.get(path, 0)}/{count}"
        for path, count in sorted(expected_counts.items())
        if actual_counts.get(path, 0) < count
    )
    return tuple(sorted(expected_stable - actual_stable)) + thinned


def _expected_nodes(
    manifest: Manifest,
) -> tuple[set[str], dict[str, int], int, int, tuple[str, ...]]:
    """Base preservation inventory, base oracle score, target oracle total,
    and the oracle nodes the target actually passed.

    Read from the task's own qualification record, which is frozen
    evidence: it is what the base and target actually did under this
    environment, so it is the only defensible reference for "did this
    candidate improve on doing nothing".
    """
    record = json.loads((manifest.task_dir / "qualification.json").read_text())
    conditions = record["conditions"]
    oracle_files = set(manifest.oracle_files)
    stable, counts = _node_census(
        node
        for node in conditions["base_preservation"]["nodes"]
        if node.split("::")[0] not in oracle_files
    )
    target_oracle = conditions["target_oracle"]
    return (
        stable,
        counts,
        int(conditions["base_oracle"]["tests_passed"]),
        int(target_oracle["tests_passed"]),
        tuple(target_oracle.get("nodes", ())),
    )


def _oracle_shortfall(
    expected_oracle_nodes: tuple[str, ...], outcomes: Mapping[str, str]
) -> tuple[str, ...]:
    """Oracle nodes the target passed that this candidate did not.

    The acceptance rule used to ask only whether the oracle suite ended
    in `reason_class == "pass"`, and pytest exits zero when tests are
    *skipped*. A candidate that caused the hidden assertions to skip --
    a `pytest.skip()` reachable from the new behaviour, a collection
    condition that excludes them -- would satisfy every other condition
    and be accepted. Nothing in the banked record did this (all 43
    accepts passed every target node), but nothing stopped it either.

    Node-level rather than a count, because a count can be restored by
    a candidate whose production change adds parametrised cases while
    the original assertion quietly stops running.
    """
    missing = []
    for node in expected_oracle_nodes:
        outcome = outcomes.get(node)
        if outcome is None:
            missing.append(f"{node} (absent)")
        elif not outcome.endswith(":passed"):
            missing.append(f"{node} ({outcome})")
    return tuple(missing)


def grade_candidate(
    manifest: Manifest,
    clone: Path,
    env: CohortEnv,
    patch: str,
    model_seconds: float = 0.0,
    model_timed_out: bool = False,
    tools: str = ENVELOPE_TOOLS,
    argv: tuple[str, ...] = (),
    suite_timeout: float = 300.0,
    executor_env_lock_sha256: str = "none",
    budget_exhausted: str = "none",
    test_paths: tuple[str, ...] = (),
    model_timeout_seconds: float = 0.0,
    validity: str = VALID,
    validity_evidence: tuple[str, ...] = (),
    reference_patch: str | None = None,
    prompt_sha256: str = "",
    cell: dict[str, str] | None = None,
) -> Attempt:
    """Score one saved candidate. Pure, offline, no model call.

    Two questions, two workspaces, and neither contaminates the other:

    - **preservation**: candidate production over the base tree, base
      tests, oracle test files ignored. No overlay at all -- overlaying
      target files here is what made a comment-only edit read as
      repository damage, because a root `conftest.py` in the oracle loads
      as a pytest plugin no matter what `--ignore` says.
    - **oracle**: candidate production plus the target's oracle files,
      which is the only place target-side tests belong.

    Both workspaces receive *production paths only*. A model-authored
    test, conftest or ini file is recorded as out-of-scope and never
    executed -- otherwise a candidate could grade itself.

    The headline number is the oracle delta over base, not acceptance. A
    candidate scoring 15/18 where the base already scores 15/18 has done
    nothing, and reporting it as a near-miss is how a floor gets mistaken
    for a middle.
    """
    manifest_hash = sha256_file(manifest.task_dir / "manifest.toml")
    (
        expected_stable,
        expected_counts,
        base_passed,
        target_total,
        expected_oracle_nodes,
    ) = _expected_nodes(manifest)

    preservation_command = tuple(manifest.preservation_command) + tuple(
        argument for entry in manifest.deselects for argument in ("--deselect", entry)
    )
    ignore_oracle = tuple(
        argument
        for oracle_file in manifest.oracle_files
        for argument in ("--ignore", oracle_file)
    )

    with materialize(clone, manifest.base_sha) as inspect:
        apply_candidate(inspect, patch)
        changed = _changed_paths(inspect)
        out_of_scope = _out_of_scope(changed, manifest.writable, test_paths)
        wrote_tests = tuple(
            path
            for path in changed
            if not _matches(path, manifest.writable) and _matches(path, test_paths)
        )

    with materialize(clone, manifest.base_sha) as preserving:
        apply_candidate(preserving, patch, include=manifest.writable)
        preservation = run_suite(
            preserving, preservation_command + ignore_oracle, env, suite_timeout
        )

    with materialize(clone, manifest.base_sha) as grading:
        apply_candidate(grading, patch, include=manifest.writable)
        overlay_oracle(clone, manifest, grading)
        oracle = run_suite(grading, manifest.oracle_command, env, suite_timeout)

    missing_nodes = _vanished(expected_stable, expected_counts, preservation.outcomes)
    oracle_shortfall = _oracle_shortfall(expected_oracle_nodes, oracle.outcomes)
    oracle_delta = oracle.tests_passed - base_passed
    gap = target_total - base_passed
    gap_closed = (oracle_delta / gap) if gap > 0 else 0.0

    preserved = preservation.reason_class == "pass" and not missing_nodes
    # Validity gates acceptance, and is checked first. A void attempt can
    # satisfy every other condition -- the stolen `autowire` candidate
    # passed preservation, passed the oracle, wrote nothing out of scope
    # and left the node inventory intact, because it was the target
    # commit's own code.
    # `reason_class == "pass"` alone was the hole: pytest exits zero on a
    # skipped test, so a candidate that made the hidden assertions skip
    # satisfied every other condition. Acceptance now requires every
    # oracle node the target passed to have passed here too.
    accepted = (
        validity == VALID
        and preserved
        and oracle.reason_class == "pass"
        and not oracle_shortfall
        and not out_of_scope
    )

    if validity != VALID:
        outcome = validity
    elif accepted:
        outcome = "accepted"
    elif missing_nodes:
        outcome = "tests-vanished"
    # Ranked directly after `tests-vanished` because it is the same
    # species: the suite reports success while the assertions that define
    # the task did not run.
    elif oracle_shortfall and oracle.reason_class == "pass":
        outcome = "oracle-incomplete"
    # Damage outranks a scope violation. `out-of-scope` reads as benign --
    # wrote in the wrong place -- and it was being reported for a candidate
    # whose own new doctest failed the suite. The first thing a reader needs
    # to know about a candidate is whether it broke the repository.
    elif not preserved and oracle_delta > 0:
        outcome = "progress-but-damaged"
    elif not preserved:
        outcome = "damaged"
    elif out_of_scope and oracle.reason_class == "pass":
        outcome = "out-of-scope"
    elif oracle_delta > 0:
        outcome = "partial-progress"
    elif oracle_delta < 0:
        outcome = "regressed"
    elif not changed:
        outcome = "no-changes"
    else:
        outcome = "no-progress"

    return Attempt(
        task_id=manifest.task_id,
        manifest_sha256=manifest_hash,
        rule_version=GRADING_RULE_VERSION,
        tools=tools,
        accepted=accepted,
        outcome=outcome,
        base_passed=base_passed,
        target_total=target_total,
        oracle_delta=oracle_delta,
        gap_closed=round(gap_closed, 3),
        missing_nodes=missing_nodes,
        oracle_shortfall=oracle_shortfall,
        changed_paths=changed,
        out_of_scope=out_of_scope,
        model_seconds=model_seconds,
        model_timed_out=model_timed_out,
        preservation=preservation,
        oracle=oracle,
        argv=argv,
        executor_env_lock_sha256=executor_env_lock_sha256,
        budget_exhausted=budget_exhausted,
        wrote_tests=wrote_tests,
        model_timeout_seconds=model_timeout_seconds,
        validity=validity,
        validity_evidence=validity_evidence,
        prompt_sha256=prompt_sha256,
        cell=dict(cell or {}),
        reference_overlap=(
            overlap(patch, reference_patch, manifest.writable_prefixes())
            if reference_patch is not None
            else -1.0
        ),
    )


def screen_task(
    manifest: Manifest,
    clone: Path,
    env: CohortEnv,
    model: str,
    tools: str = ENVELOPE_TOOLS,
    timeout: float = 900.0,
    suite_timeout: float = 300.0,
    executor_env_source: Path | None = None,
    extensions: tuple[Path, ...] = (ENVELOPE_EXTENSION,),
    test_paths: tuple[str, ...] = (),
    reference_patch: str | None = None,
    appended_prompt: str = "",
) -> tuple[Attempt, str, str]:
    """One bounded model attempt, with its candidate patch and transcript.

    The model call is the only expensive, unrepeatable step, so it happens
    once and its whole result is handed back as a patch. Everything
    downstream is `grade_candidate`, replayable offline whenever the
    acceptance rule changes -- which it has, five times.

    The transcript is returned for the same reason the patch is. A run
    that wrote nothing after nine minutes and a run that reasoned to the
    wrong answer both grade `no-changes`, and nothing in the record
    separates them: whether the executor hit the tool-call cap while
    still exploring, argued itself out of a correct edit, or never
    understood the brief are three different findings with three
    different responses, and the only place that distinction exists is
    the transcript. Discarding it makes the expensive step unrepeatable
    *and* uninterpretable.

    A candidate that changed nothing is graded like any other rather than
    short-circuited. It still has a base score, a delta of zero, and a
    preservation result, and reporting those makes "wrote nothing" and
    "wrote something useless" comparable instead of collapsing both into
    an early return.

    `executor_env_source` is the arm's environment condition, recorded on
    the attempt. `None` reproduces the bare tree the first screen ran
    against, which is now an ablation rather than the default.
    """
    brief = manifest.brief_path.read_text()
    if appended_prompt:
        # Composed here rather than written into the task directory: a
        # draft contract is an arm condition tonight, not a frozen task
        # property, and writing it into `manifest.toml` would change
        # `manifest_sha256` -- which the design calls a different task
        # wearing the same name, and would retire today's brief-only
        # cells as comparisons.
        brief = brief.rstrip() + "\n\n" + appended_prompt.strip() + "\n"
    prompt_hash = hashlib.sha256(brief.encode()).hexdigest()

    with materialize(clone, manifest.base_sha) as workspace:
        argv = _pi_command(model, brief, extensions)
        argv = argv[:-1] + ["--tools", tools] + argv[-1:]

        if executor_env_source is None:
            child_env, env_lock = pi_env(), "none"
        else:
            env_lock = provision_executor_env(workspace, executor_env_source)
            child_env = executor_env_vars(workspace)

        started = time.monotonic()
        child = run_process(argv, cwd=workspace, timeout=timeout, env=child_env)
        model_seconds = time.monotonic() - started
        patch = capture_candidate(workspace)

    # Before grading, not after: the transcript is the only artifact that
    # can say whether the patch is the model's work at all.
    validity, evidence = assess(child.stdout)

    attempt = grade_candidate(
        manifest,
        clone,
        env,
        patch,
        validity=validity,
        validity_evidence=evidence,
        model_seconds=model_seconds,
        model_timed_out=child.timed_out,
        tools=tools,
        argv=tuple(argv),
        suite_timeout=suite_timeout,
        executor_env_lock_sha256=env_lock,
        budget_exhausted=budget_exhaustion(child.stdout),
        test_paths=test_paths,
        model_timeout_seconds=timeout,
        reference_patch=reference_patch,
        prompt_sha256=prompt_hash,
        cell=resolve_cell(model, tools, extensions, timeout),
    )
    return attempt, patch, child.stdout


def write_attempt(path: Path, attempt: Attempt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(attempt.payload(), indent=2, sort_keys=True) + "\n")
