"""Build a typed `HandoffContract` + `FileBaseline[]` for the implementer extension.

Deliberately narrow, and not a general contract-authoring bridge -- the
roadmap's "bridge contracts to the typed handoff" (extending
`tools/author_contract.py` to emit `HandoffContract` JSON from the
manifest, with `inspectContract` as an admission gate) is separate,
tracked work and stays undone here. This module exists to drive the
2026-08-11 step-5 smoke set (`flask-extensions`, `stringified-annotations`,
`local-pings`, `autowire`) through the real ported engine end to end, and
now also the two arms of the pre-registered comparison in
docs/superpowers/specs/2026-08-11-phase7-cycle7-preregistration-design.md: the same
four tasks, executor and writable scope, differing only in whether
`contract.task` carries the concise brief (`task_source="brief"`) or the
complete locating contract (`task_source="locating-contract"`, the
default and everything this module ran before the pre-registration).

The gap this papers over: `HandoffContract.writableFiles` (see
`extensions/implementer/handoff-contract.ts`) requires exact,
already-existing-or-declared paths -- `normalizeContractPath` rejects a
glob outright. Three of the four smoke tasks' `candidate_output` is
already exact. `autowire`'s is deliberately the whole writable surface
(`src/svcs/**`), because naming the new module would hand the executor a
structural decision its brief does not make -- see the manifest's own
comment. `AUTOWIRE_TARGET` below is this module's own decision, made only
so the smoke set can run; it is not a claim that this is the right name,
and a real planner/contract-authoring pass would decide it properly
(roadmap Cycle 6).
"""

import hashlib
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NotRequired, TypedDict

from harness.workload import Manifest, load_manifest

type TaskSource = Literal["locating-contract", "brief"]


class WritableFile(TypedDict):
    """Mirrors `WritableFile` in extensions/implementer/handoff-contract.ts."""

    path: str


class HandoffContract(TypedDict):
    """The contract handed to the bounded implementer, as JSON.

    A structural mirror of the `HandoffContract` interface in
    `extensions/implementer/handoff-contract.ts` -- this dict is
    serialized into `SATYRN_HANDOFF_CONTRACT` and parsed back by
    `implementer.ts`'s `isContract()`, so the two definitions are one
    wire format with two declarations. Typed rather than left as
    `dict[str, object]` because that erasure was the direct cause of
    nine of the ten type errors in this repository: every reader had to
    re-narrow `object` before it could call `.startswith` or `len()` on
    a field whose type was never actually in doubt.

    Keep in sync with the TypeScript by hand. There is no generator, and
    a drift here surfaces as the child rejecting the contract at
    `isContract()` rather than as a type error on this side.
    """

    task: str
    writableFiles: list[WritableFile]
    readableFiles: list[str]
    acceptanceStrings: list[str]
    preservedBehavior: list[str]
    knownFacts: list[str]
    validation: str
    removableSymbols: NotRequired[list[str]]
    """Public symbols the writer may remove outright.

    A move needs no declaration -- the engine sees the symbol arrive in
    its destination. A rename has no compensating file, so declaring it
    is the only way to tell it from the destructive edit the engine
    exists to refuse.
    """


TASKS_DIR = Path(__file__).resolve().parents[1] / "workloads" / "svcs" / "tasks"
LOCATING_CONTRACTS_DIR = (
    Path(__file__).resolve().parents[1]
    / "workloads"
    / "svcs"
    / "contracts"
    / "locating"
)

# See the module docstring: this bridge is narrow on purpose, not merely
# untested past four tasks. Six other qualified svcs tasks (async-cm-enter,
# fastapi-get-registry, magicmock-factory, registry-iter,
# register-value-enter, suppress-context-exit) each already have an exact
# (non-glob) candidate_output and a brief.md -- confirmed by reading their
# manifests, not assumed -- so without this guard, build_typed_handoff would
# silently succeed for any of them under task_source="brief" (no locating
# contract to be missing, which is the only thing that currently makes an
# unsupported task fail loudly, and only in the locating-contract arm). A
# collaborator adding a fifth task needs an explicit decision to extend this
# tuple, not an accidental pass-through the first time they try one.
SUPPORTED_TASKS: tuple[str, ...] = (
    "flask-extensions",
    "stringified-annotations",
    "local-pings",
    "autowire",
)

# See the module docstring. Only consulted when a manifest's
# `candidate_output` contains no exact (non-glob) path.
AUTOWIRE_TARGET = "src/svcs/_autowire.py"

# The real target diff (base 816403b..target 6bb3f28) touches exactly one
# other file: src/svcs/__init__.py, a 3-line export addition
# (`from ._autowire import aautowire, autowire` plus two __all__ entries).
# Without this, the contract was structurally unsatisfiable -- the oracle
# imports `from svcs import autowire, aautowire`, which nothing written to
# AUTOWIRE_TARGET alone can supply. Confirmed against the clone, not
# guessed: this is not a claim that AUTOWIRE_TARGET's own name is right
# (see the module docstring), only that these two paths are what the real
# fix touches.
AUTOWIRE_INIT = "src/svcs/__init__.py"


class TypedContractError(Exception):
    """The manifest, locating contract, or worktree could not produce a usable handoff."""


def strip_authoring_narration(text: str) -> str:
    """Drop a locating contract's leading authoring-model narration.

    2026-08-11 morning summary: `screen_workload.py` appends draft bytes
    raw, and every locating contract in this cohort opens with a
    harmless-looking sentence like "Here is the contract:" before its
    first `---` separator. Passed untouched into a fresh executor prompt,
    that is exactly the kind of prose the mechanism screen's own findings
    warned against composing without stripping.
    """
    marker = "\n---\n"
    index = text.find(marker)
    return text[index + len(marker) :].strip() if index != -1 else text.strip()


def _task_text(task_id: str, manifest: Manifest, task_source: TaskSource) -> str:
    """The child's `contract.task` field, sourced per the requested arm.

    `brief`: the manifest's own concise, behavior-only brief.md -- names
    no file, no line, no mechanism. `locating-contract`: the complete
    human-authored contract this module has driven all along. Both are
    real, already-committed documents; this function picks between them,
    it does not author either.
    """
    if task_source == "brief":
        return manifest.brief_path.read_text().strip()
    locating_path = LOCATING_CONTRACTS_DIR / f"{task_id}.md"
    if not locating_path.is_file():
        raise TypedContractError(f"no locating contract at {locating_path}")
    return strip_authoring_narration(locating_path.read_text())


def _exact_candidate_paths(manifest: Manifest) -> tuple[str, ...]:
    exact = tuple(p for p in manifest.candidate_output if "*" not in p)
    if exact:
        return exact
    if manifest.task_id == "autowire":
        return (AUTOWIRE_TARGET, AUTOWIRE_INIT)
    raise TypedContractError(
        f"{manifest.task_id}: candidate_output has no exact path and no override is known"
    )


def _effective_preservation_command(manifest: Manifest) -> tuple[str, ...]:
    """The preservation command, minus nodes that can never pass here.

    `manifest.deselects` is qualification's own list (harness.workload.qualify
    applies the identical pattern) -- always honored.

    `manifest.rejection_failing_nodes` is a second, distinct reason to
    deselect, specific to this delivery path. Qualification always pairs
    source and tests from the *same* revision (base+base or target+target),
    so a node that legitimately differs in behavior between revisions never
    causes a conflict there. This delivery flow does not have that luxury:
    the model may only write production code, so the worktree's test files
    stay frozen at base while the source it produces implements target
    behavior -- and for a task whose target diff *changes* an existing
    assertion rather than adding a new one (flask-extensions: the base
    tests assert app.config, matching old behavior; a correct fix makes
    them false), the base test's own assertion is guaranteed to fail
    against any correct fix. `rejection_failing_nodes` is precisely the
    manifest's own list of such nodes -- confirmed for flask-extensions by
    reading the model's actual diff (all six locations changed exactly as
    specified) against the two tests that still failed. Harmless everywhere
    else: a node from this list that was never collected at base (true for
    stringified-annotations and local-pings, whose target diffs add new
    tests rather than changing existing ones) is a silent no-op for
    pytest's --deselect.
    """
    deselect = tuple(manifest.deselects) + tuple(manifest.rejection_failing_nodes)
    return tuple(manifest.preservation_command) + tuple(
        argument for node in deselect for argument in ("--deselect", node)
    )


@dataclass(frozen=True)
class TypedHandoff:
    contract: HandoffContract
    baselines: list[dict[str, object]]
    writable_glob: tuple[str, ...]
    """`deliver()`'s outer scope check, the manifest's own glob policy --
    independent of, and looser than, the contract's exact writableFiles."""
    oracle_command: tuple[str, ...]


def build_typed_handoff(
    task_id: str,
    worktree: Path,
    *,
    task_source: TaskSource = "locating-contract",
) -> TypedHandoff:
    """Assemble the contract and file baselines for one task, against one worktree.

    `worktree` must already exist at the task's base revision -- baselines
    are read from disk, not derived from the manifest, because a baseline
    is a claim about the file the child is actually about to see.

    `task_source` selects the arm (see the module docstring); it changes
    only `contract["task"]`. writableFiles, baselines and validation are
    the executor's own bounds, sourced from the manifest either way --
    the comparison this exists for is about what the model is told, not
    about loosening what it's allowed to touch.
    """
    if task_id not in SUPPORTED_TASKS:
        raise TypedContractError(
            f"{task_id!r} is not one of this bridge's four supported tasks "
            f"{SUPPORTED_TASKS!r}. This is a deliberate scope limit (see this "
            "module's docstring), not an oversight -- extending it requires "
            "a decision about the manifest-to-handoff boundary (roadmap "
            "Cycle 6), not just adding a name here."
        )
    manifest = load_manifest(TASKS_DIR / task_id)
    task_text = _task_text(task_id, manifest, task_source)

    writable_paths = _exact_candidate_paths(manifest)
    baselines: list[dict[str, object]] = []
    for relative in writable_paths:
        absolute = worktree / relative
        if absolute.is_file():
            content = absolute.read_bytes()
            baselines.append(
                {
                    "path": relative,
                    "state": "present",
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "mode": absolute.stat().st_mode & 0o777,
                    "lineEnding": "CRLF" if b"\r\n" in content else "LF",
                }
            )
        elif absolute.exists():
            raise TypedContractError(f"{relative} exists but is not a regular file")
        else:
            baselines.append({"path": relative, "state": "absent"})

    contract: HandoffContract = {
        "task": task_text,
        "writableFiles": [{"path": p} for p in writable_paths],
        "readableFiles": [],
        "acceptanceStrings": [],
        "preservedBehavior": [],
        "knownFacts": [],
        # Safe to reveal: the preservation suite, not the hidden oracle
        # command -- deliver_candidate.py's --contract-task gates on this
        # same string, not the oracle command, so what the model is told
        # the parent will run is what the parent actually runs.
        # shlex.join, not a plain " ".join: deliver_candidate.py
        # re-tokenizes this with shlex.split before handing it to
        # deliver(), and a future preservation command with a quoted or
        # spaced argument would round-trip wrong under plain whitespace
        # joining.
        "validation": shlex.join(_effective_preservation_command(manifest)),
    }
    return TypedHandoff(
        contract=contract,
        baselines=baselines,
        writable_glob=manifest.writable,
        oracle_command=manifest.oracle_command,
    )
