"""Screen a frozen replay cohort with one bounded model attempt per task.

NOT EVIDENCE. One attempt per task, no repetition, no interleaving, no
pre-registered margins. Its job is to find out whether the cohort spreads
outcomes at all -- a cohort that is entirely floor or entirely ceiling
cannot distinguish anything, however rigorously it was qualified.

The arm is brief-only: the executor sees the task brief and the base
tree. Contracts are not authored yet, so nothing here speaks to what a
complete contract would do.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import harness.cell as cell
import harness.screen as screen
import harness.workload as workload
import harness.workspace as workspace
from harness.liveness import check_model_server_alive
from harness.pi_invocation import DEFAULT_MODEL
from harness.reconstruction import contract_hash


def contract_admission(
    task_ids: Sequence[str], contract_draft_dir: Path, probe_dir: Path
) -> str:
    """Refuse-or-empty for the contract arm's gate, as a testable string.

    Empty string means every drafted task is clean and bound to a
    current probe result. Anything else is the exact refusal message
    `main` raises, so this function carries the whole decision and
    `main` only has to act on it.
    """
    unmeasured, stale, leaking = [], [], {}
    for task_id in task_ids:
        draft = contract_draft_dir / f"{task_id}.md"
        if not draft.is_file():
            continue
        result = probe_dir / f"{task_id}.json"
        if not result.is_file():
            unmeasured.append(task_id)
            continue
        payload = json.loads(result.read_text())
        # Bound to the exact bytes the probe scored, not just "a probe
        # result exists for this task name". A re-authoring loop that
        # overwrites a draft in place, or resumes into a directory
        # holding a mix of old and new attempts, must not let a stale
        # clean verdict pass a new, unmeasured draft.
        if contract_hash(draft.read_text()) != payload.get("contract_sha256"):
            stale.append(task_id)
            continue
        leaked = payload.get("leaked", [])
        if leaked:
            leaking[task_id] = leaked

    if not (unmeasured or stale or leaking):
        return ""
    report = []
    if leaking:
        report.append(
            f"{len(leaking)} contract(s) disclose the fix:\n"
            + "\n".join(f"  {t}: {', '.join(sig[:4])}" for t, sig in sorted(leaking.items()))
        )
    if stale:
        report.append(
            f"{len(stale)} contract(s) changed since their leak-probe result "
            f"was recorded: {', '.join(stale)}\n"
            "  Re-run tools.leak_probe against the current draft. A hash "
            "mismatch means the probe scored different bytes than the ones "
            "about to enter this arm."
        )
    if unmeasured:
        report.append(
            f"{len(unmeasured)} contract(s) have no leak-probe result in "
            f"{probe_dir}: {', '.join(unmeasured)}\n"
            "  Run tools.leak_probe first. An unmeasured contract is not a "
            "clean one."
        )
    return "\n\n".join(report)


def reference_for(task_id: str, root: Path = Path("workloads/svcs/reference-patches")):
    """The saved target patch for this task, when it exists.

    Read from disk rather than recomputed, so the overlap number is
    computed against a fixed artifact rather than a re-derived one.

    These patches were produced by `tools/ceiling_replay.py`, deleted
    2026-08-12 as unreferenced. The patches it wrote are still committed
    under `workloads/svcs/reference-patches/` and are still read here;
    only the generator is gone. Regenerating them would mean restoring
    that tool from git history.
    """
    path = root / f"{task_id}.patch"
    return path.read_text() if path.is_file() else None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True, type=Path)
    parser.add_argument("--cache", type=Path, default=Path(".workloads"))
    parser.add_argument("--task", action="append", default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--server",
        default="http://127.0.0.1:8001",
        help=(
            "model server to liveness-check; must match the provider baseUrl "
            "the --model prefix resolves to in pi-agent-dir/models.json"
        ),
    )
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument(
        "--allow-stale-workspaces",
        action="store_true",
        help="run despite leftover workspaces in the temp dir (unsafe)",
    )
    parser.add_argument(
        "--contract-draft-dir",
        type=Path,
        default=None,
        help=(
            "append <dir>/<task_id>.md to each brief. The arm name and the "
            "composed prompt hash are recorded; task manifests are untouched, "
            "so brief-only cells stay comparable under their frozen hashes"
        ),
    )
    parser.add_argument(
        "--probe-dir",
        type=Path,
        default=None,
        help="leak-probe results; defaults to <contract-draft-dir>/probe",
    )
    parser.add_argument(
        "--guards",
        action="store_true",
        help=(
            "load the shipped loop breaker alongside the budget cap. This is "
            "a different cell, not the same arm with a helper: the extension "
            "set is part of what defines an arm"
        ),
    )
    parser.add_argument(
        "--proposal-limit",
        action="store_true",
        help=(
            "load the 32KB write-size refusal alongside the envelope cap. "
            "Opt-in, not default: stage 2 and stage 5 ran without it, and "
            "auto-including it would silently stop `gemma12b-envelope.toml` "
            "from reproducing the arm those results were recorded under. "
            "Use `gemma12b-envelope-v2.toml` for this"
        ),
    )
    parser.add_argument(
        "--cell",
        type=Path,
        default=None,
        help=(
            "a cell manifest under workloads/svcs/cells/. The live "
            "configuration is verified against it before any model call, and "
            "the run aborts on a mismatch rather than recording a number that "
            "disagrees with reality"
        ),
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help=(
            "use probe-cap.ts budgets (60 turns / 150 tools) instead of the "
            "16/30 envelope. The envelope mirrors the engine's implementer "
            "child and was calibrated for read,write with no execution; a "
            "headroom probe that a budget truncates measures the budget"
        ),
    )
    parser.add_argument(
        "--blind",
        action="store_true",
        help=(
            "withhold the dev environment from the executor (ablation). "
            "The default gives it the cohort's dependencies, because "
            "routine work happens in a repository that has an environment"
        ),
    )
    parser.add_argument(
        "--tools",
        default=screen.ENVELOPE_TOOLS,
        help="Pi tool allowlist for the arm (default: Phase 7-pre's read,write)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("workloads/svcs/screen"),
        help="where per-task attempt records are written",
    )
    args = parser.parse_args(argv)

    # Before anything else, and before a single model call: a workspace
    # left behind by an earlier run is an answer key for every task whose
    # base predates it, and the executor has a shell and a listable temp
    # directory. Cycle 1 lost its ceiling task to exactly this.
    stale = workspace.stale_workspaces()
    if stale and not args.allow_stale_workspaces:
        raise SystemExit(
            f"{len(stale)} stale workspace(s) in the shared temp directory:\n"
            + "\n".join(f"  {p}" for p in stale[:10])
            + "\n\nEach was materialized from some base commit and contains that "
            "commit's tree, so any of them may hold another task's answer. Move "
            "or remove them, then re-run. --allow-stale-workspaces overrides, and "
            "every attempt from such a run must be audited before it is believed."
        )

    extensions = (screen.PROBE_EXTENSION,) if args.probe else (screen.ENVELOPE_EXTENSION,)
    if args.proposal_limit:
        extensions += (screen.PROPOSAL_LIMIT_EXTENSION,)
    if args.guards:
        extensions += (screen.GUARD_EXTENSION,)
    if args.cell is not None:
        # Before liveness and before the first call: a mismatch here means
        # the run is not the arm it says it is, and every attempt it
        # produces would be mislabelled.
        declared = cell.load_cell(args.cell)
        declared.verify(
            screen.resolve_cell(args.model, args.tools, extensions, args.timeout)
        )
        print(f"cell {declared.name}: live configuration verified", flush=True)

    check_model_server_alive(args.server)
    cohort = workload.load_cohort(args.cohort, require_accounting=True)
    task_ids = args.task or list(cohort.included)

    if args.contract_draft_dir is not None:
        # Admission is the leak probe's decision, and it is checked here
        # rather than trusted to have happened. A contract that discloses the
        # fix turns this arm into a transcription measurement, which is the
        # exact result the whole planner-output decision exists to avoid.
        #
        # Counting fenced statements was tried here first and withdrawn: it
        # rejected a draft whose three "statements" were the file's existing
        # import line and two caller-side examples, and it passed a draft
        # that gave away the fix in an English sentence. Wrong in both
        # directions, on the same task, one run apart.
        #
        # A missing probe result is refusal, not a pass. Unmeasured is the
        # state every contaminated arm has been in.
        probe_dir = args.probe_dir or (args.contract_draft_dir / "probe")
        refusal = contract_admission(task_ids, args.contract_draft_dir, probe_dir)
        if refusal:
            raise SystemExit(refusal)

    clone = workload.ensure_clone(cohort.upstream, args.cache)
    env = workload.ensure_cohort_env(cohort.env_dir, args.cache)

    rows = []
    for task_id in task_ids:
        print(f"{task_id:26} running...", flush=True)
        manifest = workload.load_manifest(cohort.task_dir(task_id))
        appended = ""
        if args.contract_draft_dir is not None:
            draft = args.contract_draft_dir / f"{task_id}.md"
            if not draft.is_file():
                # Skipping silently would put a brief-only attempt in a
                # contract directory and average the two together.
                raise SystemExit(f"no contract draft for {task_id} at {draft}")
            appended = draft.read_text()
        attempt, patch, transcript = screen.screen_task(
            manifest,
            clone,
            env,
            args.model,
            tools=args.tools,
            timeout=args.timeout,
            executor_env_source=None if args.blind else cohort.env_dir,
            extensions=extensions,
            test_paths=cohort.test_paths,
            reference_patch=reference_for(task_id),
            appended_prompt=appended,
        )
        # The patch is what a later grading change replays against; the
        # transcript is what a later *reading* replays against. Both cost
        # one model call to produce and nothing to keep, and a result
        # neither can be regraded nor explained is worth very little.
        screen.write_attempt(args.out / f"{task_id}.json", attempt)
        (args.out / f"{task_id}.patch").write_text(patch)
        (args.out / f"{task_id}.jsonl").write_text(transcript)
        rows.append(attempt)
        oracle = attempt.oracle
        detail = (
            f"oracle {oracle.tests_passed}/{len(oracle.outcomes)}"
            if oracle is not None
            else "no changes written"
        )
        flag = " OUT-OF-SCOPE" if attempt.out_of_scope else ""
        if attempt.wrote_tests:
            flag += " +tests"
        if attempt.budget_exhausted != "none":
            flag += f" BUDGET:{attempt.budget_exhausted}"
        print(
            f"{task_id:26} {'ACCEPT' if attempt.accepted else 'reject':7} "
            f"{attempt.outcome:24} {detail:22} {attempt.model_seconds:6.1f}s{flag}"
        )

    accepted = sum(1 for r in rows if r.accepted)
    print(f"\n{accepted}/{len(rows)} accepted")
    (args.out / "summary.json").write_text(
        json.dumps(
            {
                "model": args.model,
                "server": args.server,
                "arm": (
                    f"{'draft-contract' if args.contract_draft_dir else 'brief-only'}"
                    f":{args.tools}:{'blind' if args.blind else 'env'}"
                ),
                "tools": args.tools,
                "executor_env": "none" if args.blind else str(cohort.env_dir),
                "budgets": "probe" if args.probe else "envelope",
                "cell": str(args.cell) if args.cell else "unpinned",
                "accepted": accepted,
                # Void attempts leave the denominator. `attempted` counted
                # them, so cycle1's stolen `autowire` made an honest 2/7
                # read as 2/8 in the authoritative-looking summary while
                # the reporting CLI excluded it correctly -- two numbers
                # for one cell, and the wrong one written to disk.
                "attempted": sum(1 for r in rows if r.validity == "valid"),
                "void": sum(1 for r in rows if r.validity != "valid"),
                "outcomes": {r.task_id: r.outcome for r in rows},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
