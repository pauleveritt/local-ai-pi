"""Drive the Cycle 7 confirmatory comparison.

Runs exactly what
docs/superpowers/specs/2026-08-11-phase7-cycle7-preregistration-design.md
pre-registers: 2 arms x 4 tasks x n=8 by default, interleaved A, B, A, B
within each repetition, one `models.json` max-tokens bump for the whole
batch, void attempts replaced (not dropped, not silently pooled with the
denominator), `oracle-passed` as the primary metric.

    uv run python -m tools.run_cycle7_confirmatory_batch --out-dir /path/to/out

Checked in per the 2026-08-11 distribution brief's step 4 ("give the
running comparison a discoverable checked-in driver"), after the batch it
originally ran (`bf01r14bi`, 2026-08-11, results at
docs/superpowers/research/2026-08-11-phase7-cycle7-confirmatory-result.md)
had already completed as a one-time uncommitted script. Behavior is
unchanged from that run except for the two things distribution required:
no hardcoded absolute worktree path, and an explicit `--out-dir` instead
of a scratchpad directory outside the repository. Re-running this against
the same commit and cell reproduces the same experiment; it does not
retroactively become part of that result's own evidence archive (a
re-run is a new, separate batch, pre-registration permitting).

Requires a live Pi/model server per `docs/superpowers/specs/
2026-08-09-phase7-cycle1-svcs-workload-design.md`'s liveness discipline --
not something a default `pytest` run exercises. `--n` and `--task` exist
for a cheaper partial rehearsal (a single task, n=1) before committing to
the full 64-attempt batch; the pre-registration's own n=8 across all four
tasks is what any batch presented as *the* confirmatory result must use.

On first run this provisions the two gitignored, derived inputs it needs
(`bootstrap_cache()`: a bare clone of the cohort upstream under
`.workloads/svcs.git`, and the frozen cohort interpreter under
`.workloads/env`), which takes ~20 seconds and needs network access for
the clone. Subsequent runs reuse both.
"""

import argparse
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import harness.candidate as candidate_mod
import tools.deliver_candidate as deliver_candidate
from harness.intervals import newcombe_interval, wilson_interval
from harness.model_config import bumped_max_tokens
from harness.workload import (
    ensure_clone,
    ensure_cohort_env,
    export_tree,
    load_cohort,
    load_manifest,
    overlay_oracle,
)
from harness.workspace import disposable_dir, git_init_commit

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / ".workloads"
CLONE = CACHE / "svcs.git"
COHORT_PYTHON_BIN = (CACHE / "env" / "bin").resolve()
COHORT_TOML = REPO / "workloads" / "svcs" / "cohort.toml"
TASKS_DIR = REPO / "workloads" / "svcs" / "tasks"
CELL = REPO / "workloads" / "svcs" / "cells" / "gemma12b-implementer-v1.toml"
AGENT_DIR = REPO / "pi-agent-dir"

# (task_id, base_sha) -- the pre-registration's frozen four-task cohort.
# See docs/superpowers/specs/2026-08-11-phase7-cycle7-preregistration-design.md,
# "Frozen task manifest and contract versions".
TASKS: tuple[tuple[str, str], ...] = (
    ("flask-extensions", "85827a173fd7b9952abf34a8f198c7d1fb40f43d"),
    ("stringified-annotations", "4b05ab8465f3d9a5ce7d1e40eaf808b0cb92a26c"),
    ("local-pings", "31bc6dfd5d1a570b3b96cfefd878ccc686bde980"),
    ("autowire", "816403b5c1d3b9fff22bd9141fe836221dfe9d9c"),
)
ARMS: tuple[str, ...] = ("brief", "locating-contract")
MAX_VOID_RETRIES_PER_SLOT = 2
BUMPED_MODEL = "gemma-4-12B-it-MLX-8bit"
BUMPED_MAX_TOKENS = 32768

_real_deliver = candidate_mod.deliver


def bootstrap_cache() -> None:
    """Create the two derived, gitignored inputs this batch reads.

    `.workloads/svcs.git` (a bare clone of the cohort's upstream) and
    `.workloads/env` (the frozen cohort interpreter) are deliberately not
    committed -- every manifest names its upstream and SHAs, so both are
    reconstructible, and `.gitignore` says they must never be committed.
    But nothing here created them either: before this function existed, a
    fresh clone running this driver died on a bare
    `FileNotFoundError: .../.workloads/svcs.git` from deep inside
    `subprocess`, with no message saying what was missing or how to get
    it. Found by cloning the curated export and running this tool as a
    collaborator would (2026-08-12).

    Both helpers are idempotent -- `ensure_clone` returns early if the
    clone exists, `ensure_cohort_env` runs `uv sync --locked` -- so this
    costs a few seconds on an already-provisioned checkout and does the
    one-time ~20s setup otherwise.
    """
    cohort = load_cohort(COHORT_TOML)
    if not CLONE.is_dir():
        print(f"provisioning {CLONE} from {cohort.upstream} (one time)...", flush=True)
    ensure_clone(cohort.upstream, CACHE)
    if not COHORT_PYTHON_BIN.is_dir():
        print(f"provisioning the cohort environment under {CACHE / 'env'} (one time)...", flush=True)
    ensure_cohort_env(cohort.env_dir, CACHE)


def cohort_env(pythonpath: Path) -> dict[str, str]:
    return {
        "PATH": f"{COHORT_PYTHON_BIN}:{os.defpath}",
        "PYTHONPATH": str(pythonpath),
        "PYTHONDONTWRITEBYTECODE": "1",
        "HOME": os.environ.get("HOME", ""),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
    }


def oracle_check(git_dir: Path, candidate_commit: str, manifest) -> dict:
    with disposable_dir("confirmatory-oraclecheck-") as grading:
        result = subprocess.run(
            ["git", f"--git-dir={git_dir}", "archive", "--format=tar", candidate_commit],
            capture_output=True,
        )
        if result.returncode != 0:
            return {"ran": False, "error": result.stderr.decode(errors="replace")}
        with tarfile.open(fileobj=io.BytesIO(result.stdout)) as tar:
            tar.extractall(grading, filter="data")
        overlay_oracle(CLONE, manifest, grading)
        proc = subprocess.run(
            list(manifest.oracle_command),
            cwd=grading,
            env=cohort_env(grading / "src"),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {"ran": True, "returncode": proc.returncode, "tail": (proc.stdout + proc.stderr)[-1500:]}


def run_one(task_id: str, base_sha: str, arm: str, label: str, out_dir: Path) -> dict:
    """One attempt. Returns a result dict, including void=True/False."""
    manifest = load_manifest(TASKS_DIR / task_id)
    with disposable_dir(f"confirmatory-{task_id}-") as workspace:
        export_tree(CLONE, base_sha, workspace)
        git_init_commit(workspace, f"materialized base {base_sha}")
        worktree = workspace / ".git" / "satyrn-worktrees" / task_id
        validation_env = cohort_env(worktree / "src")

        receipt_path = out_dir / f"{label}.json"

        def patched_deliver(*args, **kwargs):
            kwargs["validation_env"] = validation_env
            return _real_deliver(*args, **kwargs)

        candidate_mod.deliver = patched_deliver
        deliver_candidate.deliver = patched_deliver
        try:
            rc = deliver_candidate.main([
                "--repo", str(workspace),
                "--task", task_id,
                "--contract-task", task_id,
                "--task-source", arm,
                "--cell", str(CELL),
                "--agent-dir", str(AGENT_DIR),
                "--receipt", str(receipt_path),
            ])
        except Exception as exc:  # noqa: BLE001 -- void classification below
            return {"label": label, "task": task_id, "arm": arm, "void": True, "void_reason": f"exception: {exc}"}
        finally:
            candidate_mod.deliver = _real_deliver
            deliver_candidate.deliver = _real_deliver

        if not receipt_path.is_file():
            return {"label": label, "task": task_id, "arm": arm, "void": True, "void_reason": f"no receipt, rc={rc}"}

        payload = json.loads(receipt_path.read_text())
        if payload["outcome"] == "infrastructure-failure":
            return {"label": label, "task": task_id, "arm": arm, "void": True, "void_reason": payload.get("refusal", "infrastructure-failure")}

        oracle = None
        if payload.get("outcome") == "candidate-created":
            oracle = oracle_check(workspace / ".git", payload["candidate_commit"], manifest)

        return {
            "label": label, "task": task_id, "arm": arm, "void": False,
            "outcome": payload["outcome"], "oracle": oracle,
            "oracle_passed": bool(oracle and oracle.get("returncode") == 0),
        }


def run_slot(task_id: str, base_sha: str, arm: str, rep: int, out_dir: Path) -> dict:
    """Run one pre-registered (task, arm, rep) slot, replacing void attempts."""
    for attempt in range(1 + MAX_VOID_RETRIES_PER_SLOT):
        label = f"{task_id}__{arm}__r{rep}" + (f"__retry{attempt}" if attempt else "")
        print(f"=== {label} ===", flush=True)
        result = run_one(task_id, base_sha, arm, label, out_dir)
        if not result["void"]:
            return result
        print(f"    VOID: {result['void_reason']} -- replacing", flush=True)
    result["void_exhausted"] = True
    return result


def run_batch(tasks: tuple[tuple[str, str], ...], n_per_arm: int, out_dir: Path) -> list[dict]:
    results = []
    with bumped_max_tokens(BUMPED_MODEL, BUMPED_MAX_TOKENS):
        for task_id, base_sha in tasks:
            for rep in range(1, n_per_arm + 1):
                for arm in ARMS:  # A, B interleaved within each rep
                    result = run_slot(task_id, base_sha, arm, rep, out_dir)
                    results.append(result)
                    print(
                        f"    -> void={result['void']} outcome={result.get('outcome')} "
                        f"oracle_passed={result.get('oracle_passed')}",
                        flush=True,
                    )
    return results


def report(tasks: tuple[tuple[str, str], ...], results: list[dict], out_dir: Path) -> None:
    print("\n\n==================== REPORT ====================")
    void_count = sum(1 for r in results if r.get("void_exhausted"))
    print(f"attempts: {len(results)}  unresolved-void: {void_count}\n")

    by_task_arm: dict[tuple[str, str], list[dict]] = {}
    for r in results:
        if r["void"]:
            continue
        by_task_arm.setdefault((r["task"], r["arm"]), []).append(r)

    for task_id, _ in tasks:
        print(f"--- {task_id} ---")
        rates = {}
        for arm in ARMS:
            rs = by_task_arm.get((task_id, arm), [])
            created = sum(1 for r in rs if r.get("outcome") == "candidate-created")
            passed = sum(1 for r in rs if r.get("oracle_passed"))
            n = len(rs)
            rates[arm] = (passed, n)
            interval = wilson_interval(passed, n)
            print(f"  {arm:18s} n={n} created={created} oracle_passed={passed}  [{interval.low:.2f},{interval.high:.2f}]")
        (pb, nb) = rates.get("locating-contract", (0, 0))
        (pa, na) = rates.get("brief", (0, 0))
        if na and nb:
            diff = newcombe_interval(pb, nb, pa, na)
            verdict = (
                "SUPERIORITY (contract > brief)" if diff.excludes_zero_above()
                else "reverse separation (brief > contract)" if diff.excludes_zero_below()
                else "INCONCLUSIVE"
            )
            print(f"  difference (contract - brief): [{diff.low:.2f},{diff.high:.2f}]  {verdict}")
        print()

    print(f"full results: {out_dir / 'all_results.json'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--out-dir", type=Path, required=True,
        help="directory for per-attempt receipts and all_results.json; created if absent",
    )
    parser.add_argument(
        "--n", type=int, default=8,
        help="repetitions per arm per task (pre-registration default: 8; "
        "use a smaller value only for a rehearsal, never to present as the confirmatory result)",
    )
    parser.add_argument(
        "--task", choices=[t for t, _ in TASKS], default=None,
        help="restrict to one task (for a rehearsal); omit to run the full four-task cohort",
    )
    args = parser.parse_args(argv)

    tasks = TASKS if args.task is None else tuple(t for t in TASKS if t[0] == args.task)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    bootstrap_cache()

    results = run_batch(tasks, args.n, args.out_dir)
    (args.out_dir / "all_results.json").write_text(json.dumps(results, indent=2, sort_keys=True))
    report(tasks, results, args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
