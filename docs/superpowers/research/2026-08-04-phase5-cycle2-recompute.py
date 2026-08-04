"""Recompute phase 5 cycle 2's tables from the two checkpoints.

Child costs come from `harness.telemetry` as of phase 5 cycle 3. They were
briefly computed by a helper local to this file, which is how cycle 2's
1.15x error was corrected -- but a workaround living in one research script
protects one document, so the parsing moved into the instrument. The numbers
are unchanged by that move, and the plan required checking rather than
assuming it.

Committed so the published table cannot silently diverge from its source,
per phase 2 cycle 4's claim discipline. Run it and paste; do not hand-edit
the numbers in the research record.

    PYTHONPATH=. uv run python \
        docs/superpowers/research/2026-08-04-phase5-cycle2-recompute.py

`PYTHONPATH=.` follows the two phase 2 recompute scripts beside this one:
these live under `docs/`, so `harness` is not importable without it.

The checkpoints live outside version control in `~/local-ai-pi-evidence/`,
so this script reports what it could not find rather than failing silently.
"""

import json
import statistics
from pathlib import Path

from harness.checkpoint import load_checkpoint
from harness.telemetry import read_telemetry

EVIDENCE = Path.home() / "local-ai-pi-evidence"
ARMS = {
    "bare": EVIDENCE / "satyrn-phase5-cycle2-bare-n16.jsonl",
    "sdd-orchestrator": EVIDENCE / "satyrn-phase5-cycle2-sdd-orchestrator-n16.jsonl",
}


def delegation(pi_stdout: str) -> tuple[int, int, int]:
    """(successful subagent calls, failed subagent calls, max concurrent).

    Concurrency is computed by walking `tool_execution_start` /
    `tool_execution_end` in stream order and tracking how many `subagent`
    calls are open at once. Counting calls per turn would not distinguish
    two sequential delegations from two simultaneous ones, and the whole
    point of the observation is whether the shipped extension puts more
    than one child on a single-threaded server.
    """
    open_ids: set[str] = set()
    subagent_ids: set[str] = set()
    succeeded = failed = concurrent = 0
    for line in pi_stdout.split("\n"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("toolName") != "subagent":
            continue
        call_id = event.get("toolCallId")
        if event.get("type") == "tool_execution_start":
            subagent_ids.add(call_id)
            open_ids.add(call_id)
            concurrent = max(concurrent, len(open_ids))
        elif event.get("type") == "tool_execution_end":
            open_ids.discard(call_id)
            # `isError` alone is not enough. Pi's subagent extension rejects a
            # malformed call with `"Invalid parameters. Provide exactly one
            # mode."` as a **non-error** end carrying an empty `results[]` --
            # no child ran. Counting those as successes inflated this column
            # and produced the claim "0 failed delegations, 16/16 successful"
            # when cycle 2 run 13's only completed call was a rejection.
            # A delegation succeeded only if a child's usage came back.
            details = event.get("result", {}).get("details") or {}
            if event.get("isError") or not (details.get("results") or []):
                failed += 1
            else:
                succeeded += 1
    return succeeded, failed, concurrent


def main() -> None:
    summaries = {}
    for arm, path in ARMS.items():
        if not path.is_file():
            print(f"## {arm}\n\nMISSING: {path}\n")
            continue
        records = load_checkpoint(path)
        print(f"## {arm} — n={len(records)}\n")
        print(
            "| # | accepted | parent turns | child turns | total turns | "
            "parent ctx | child ctx | total ctx | total output | "
            "subagent ok | failed | max concurrent |"
        )
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")
        rows = []
        for i, record in enumerate(records, 1):
            t = read_telemetry(record.pi_stdout)
            ok, bad, conc = delegation(record.pi_stdout)
            cctx, cout, cturns = (
                t.child_context_processed,
                t.child_output_tokens,
                t.child_turns,
            )
            total = dict(
                turns=t.total_turns,
                ctx=t.total_context_processed,
                out=t.total_output_tokens,
            )
            rows.append((record.accepted, t, ok, bad, conc, cctx, cout, cturns, total))
            print(
                f"| {i} | {record.accepted} | {t.turns} | {cturns} | {total['turns']} | "
                f"{t.context_processed} | {cctx} | {total['ctx']} | {total['out']} | "
                f"{ok} | {bad} | {conc} |"
            )
        print()

        delegated = [r for r in rows if r[2] > 0]
        summaries[arm] = (rows, delegated)
        print(f"- accepted: {sum(1 for r in rows if r[0])}/{len(rows)}")
        print(f"- runs with >=1 successful delegation: {len(delegated)}/{len(rows)}")
        print(f"- runs with a failed delegation: {sum(1 for r in rows if r[3] > 0)}")
        print(f"- max concurrent subagent calls, any run: {max((r[4] for r in rows), default=0)}")
        for label, values in (
            ("total turns (parent+child)", [r[8]["turns"] for r in rows]),
            ("total context_processed", [r[8]["ctx"] for r in rows]),
            ("total output_tokens", [r[8]["out"] for r in rows]),
            ("parent-only context_processed", [r[1].context_processed for r in rows]),
        ):
            print(
                f"- {label}: median {statistics.median(values):.0f}, "
                f"min {min(values)}, max {max(values)}"
            )
        print()

    if len(summaries) == 2:
        print("## Paired comparison\n")
        bare_rows = summaries["bare"][0]
        orch_rows, orch_delegated = summaries["sdd-orchestrator"]
        # Compare the orchestrated arm's *actually delegated* runs only. A
        # run whose delegation never succeeded is a bare run wearing the
        # improvement's name -- cycle 1's spike found exactly that, and
        # including it would understate the orchestration's cost.
        pool = orch_delegated if orch_delegated else orch_rows
        note = "delegated runs only" if orch_delegated else "ALL runs (none delegated)"
        print(f"Orchestrated arm pool: {note}, n={len(pool)}\n")
        for label, get in (
            ("total turns", lambda r: r[8]["turns"]),
            ("total context_processed", lambda r: r[8]["ctx"]),
            ("total output_tokens", lambda r: r[8]["out"]),
            ("parent-only context_processed", lambda r: r[1].context_processed),
        ):
            b = statistics.median([get(r) for r in bare_rows])
            o = statistics.median([get(r) for r in pool])
            ratio = (o / b) if b else float("nan")
            print(f"- {label}: bare {b:.0f} vs orchestrated {o:.0f} — ratio {ratio:.2f}x")


if __name__ == "__main__":
    main()
