"""Build a typed `HandoffContract` + `FileBaseline[]` for the implementer extension.

Deliberately narrow, and not a general contract-authoring bridge -- the
roadmap's "bridge contracts to the typed handoff" (extending
`tools/author_contract.py` to emit `HandoffContract` JSON from the
manifest, with `inspectContract` as an admission gate) is separate,
tracked work and stays undone here. This module exists only to drive the
2026-08-11 step-5 smoke set (`flask-extensions`, `stringified-annotations`,
`local-pings`, `autowire`) through the real ported engine end to end.

The gap this papers over: `HandoffContract.writableFiles` (see
`extensions/orchestration/handoff-contract.ts`) requires exact,
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
from dataclasses import dataclass
from pathlib import Path

from harness.workload import Manifest, load_manifest

TASKS_DIR = Path(__file__).resolve().parents[1] / "workloads" / "svcs" / "tasks"
LOCATING_CONTRACTS_DIR = (
    Path(__file__).resolve().parents[1] / "workloads" / "svcs" / "contracts" / "locating"
)

# See the module docstring. Only consulted when a manifest's
# `candidate_output` contains no exact (non-glob) path.
AUTOWIRE_TARGET = "src/svcs/_autowire.py"


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
    return text[index + len(marker):].strip() if index != -1 else text.strip()


def _exact_candidate_paths(manifest: Manifest) -> tuple[str, ...]:
    exact = tuple(p for p in manifest.candidate_output if "*" not in p)
    if exact:
        return exact
    if manifest.task_id == "autowire":
        return (AUTOWIRE_TARGET,)
    raise TypedContractError(
        f"{manifest.task_id}: candidate_output has no exact path and no override is known"
    )


def _sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class TypedHandoff:
    contract: dict[str, object]
    baselines: list[dict[str, object]]
    writable_glob: tuple[str, ...]
    """`deliver()`'s outer scope check, the manifest's own glob policy --
    independent of, and looser than, the contract's exact writableFiles."""
    oracle_command: tuple[str, ...]


def build_typed_handoff(task_id: str, worktree: Path) -> TypedHandoff:
    """Assemble the contract and file baselines for one task, against one worktree.

    `worktree` must already exist at the task's base revision -- baselines
    are read from disk, not derived from the manifest, because a baseline
    is a claim about the file the child is actually about to see.
    """
    manifest = load_manifest(TASKS_DIR / task_id)
    locating_path = LOCATING_CONTRACTS_DIR / f"{task_id}.md"
    if not locating_path.is_file():
        raise TypedContractError(f"no locating contract at {locating_path}")
    task_text = strip_authoring_narration(locating_path.read_text())

    writable_paths = _exact_candidate_paths(manifest)
    baselines: list[dict[str, object]] = []
    for relative in writable_paths:
        absolute = worktree / relative
        if absolute.is_file():
            content = absolute.read_bytes()
            baselines.append({
                "path": relative,
                "state": "present",
                "sha256": hashlib.sha256(content).hexdigest(),
                "mode": absolute.stat().st_mode & 0o777,
                "lineEnding": "CRLF" if b"\r\n" in content else "LF",
            })
        elif absolute.exists():
            raise TypedContractError(f"{relative} exists but is not a regular file")
        else:
            baselines.append({"path": relative, "state": "absent"})

    contract = {
        "task": task_text,
        "writableFiles": [{"path": p} for p in writable_paths],
        "readableFiles": [],
        "acceptanceStrings": [],
        "preservedBehavior": [],
        "knownFacts": [],
        # Safe to reveal: the preservation suite, not the hidden oracle
        # command deliver() actually gates on below.
        "validation": " ".join(manifest.preservation_command),
    }
    return TypedHandoff(
        contract=contract,
        baselines=baselines,
        writable_glob=manifest.writable,
        oracle_command=manifest.oracle_command,
    )
