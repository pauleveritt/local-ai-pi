"""Recompute this cycle's per-run table and aggregates from the clean
baseline checkpoints. Not a test -- a reproducibility aid the research
record cites, since its claims come from parsing pi_stdout via
read_telemetry, not from a trivial line count.

Usage (from the repo root, so `harness` is importable):
    PYTHONPATH=. uv run python \\
        docs/superpowers/research/2026-08-02-phase2-cycle3-recompute-summary.py \\
        ~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-part1-n13.jsonl \\
        ~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-part2-n19.jsonl

Two checkpoints rather than one, for the reason the research record
alongside this script documents: a commit from a concurrent session moved
HEAD 13 runs in, `run_batch` correctly aborted, and the remaining 19 were
run under the new revision. The raw checkpoints are outside Git (see the
record for their checksums); this script cannot run without them.
"""

import json
import sys
from collections import Counter
from pathlib import Path

from harness.telemetry import read_telemetry


def message_span(pi_stdout: str) -> float | None:
    starts = []
    for line in pi_stdout.split("\n"):
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("type") == "message_start":
            ts = event.get("message", {}).get("timestamp")
            if ts is not None:
                starts.append(ts)
    if len(starts) < 2:
        return None
    return (max(starts) - min(starts)) / 1000.0


def load(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        tel = read_telemetry(data["pi_stdout"])
        rows.append(
            {
                "turns": tel.turns,
                "tool_calls": len(tel.tool_calls),
                "tool_names": Counter(tc.name for tc in tel.tool_calls),
                "errors": tel.tool_errors,
                "context_processed": tel.context_processed,
                "complete": tel.complete,
                "span": message_span(data["pi_stdout"]),
                # The Pi-exit veto (cycle 15), not grade.accepted alone.
                "accepted": (
                    not data["pi_timed_out"]
                    and data["pi_returncode"] == 0
                    and data["grade"]["accepted"]
                ),
                "refused": bool(data["grade"]["refused_config"]),
                "ran_a_test": ran_a_test(data["pi_stdout"]),
            }
        )
    return rows


def ran_a_test(pi_stdout: str) -> bool:
    """Did this run actually invoke pytest?

    The finding that motivated cycle 3 was that all 20 zero-error runs in
    the 48-run baseline reached zero errors by never running a test at
    all. An error count near zero is therefore not on its own evidence
    that the environment fix worked -- it is the same number the old
    skip-verification shape produced. This reads the bash commands out of
    the stream so the record can report both.

    Restricted to `bash` deliberately. Matching "pytest" across every
    tool's args would count a `write` whose file *content* mentions
    pytest -- which a test file routinely does -- and would report the
    old skip-verification runs as having tested.
    """
    for line in pi_stdout.split("\n"):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "tool_execution_start":
            continue
        if event.get("toolName") != "bash":
            continue
        if "pytest" in event.get("args", {}).get("command", ""):
            return True
    return False


def support_coverage(turns: list[int]) -> tuple[set[int], bool]:
    """Distinct turn values first seen in the final quarter of the batch.

    One-sided: a quiet final quarter is NOT evidence that the support is
    covered. The n=16 baseline is the proof -- its own runs 13-16
    introduced no new value, yet 10 and 12 were still unseen and
    surfaced at runs 17 and 20.
    """
    cut = len(turns) - len(turns) // 4
    earlier = set(turns[:cut])
    late_new = {t for t in turns[cut:] if t not in earlier}
    return late_new, bool(late_new)


def main(*checkpoint_paths: str) -> None:
    rows: list[dict] = []
    for path in checkpoint_paths:
        rows += load(Path(path))
    for i, r in enumerate(rows, 1):
        tools = ",".join(f"{k}x{v}" for k, v in sorted(r["tool_names"].items()))
        span = f"{r['span']:.1f}s" if r["span"] is not None else "n/a"
        print(
            f"{i:>2}: turns={r['turns']:>2} tools={r['tool_calls']:>2} ({tools:<19}) "
            f"errors={r['errors']} ctx={r['context_processed']:>6} "
            f"span={span:>6} complete={r['complete']} accepted={r['accepted']} "
            f"tested={r['ran_a_test']}"
        )
    turns = [r["turns"] for r in rows]
    ctx = [r["context_processed"] for r in rows]
    spans = [r["span"] for r in rows if r["span"] is not None]
    tools = sum((r["tool_names"] for r in rows), Counter())
    late_new, uncovered = support_coverage(turns)
    print()
    print("runs:", len(rows))
    print("turn distribution:", dict(sorted(Counter(turns).items())))
    print("mean turns:", sum(turns) / len(turns))
    print("tool totals:", dict(tools))
    print("total tool calls:", sum(r["tool_calls"] for r in rows))
    print("total errors:", sum(r["errors"] for r in rows))
    print("runs with >=1 error:", sum(1 for r in rows if r["errors"]))
    print("runs that ran a test:", sum(1 for r in rows if r["ran_a_test"]))
    print("all complete:", all(r["complete"] for r in rows))
    print("accepted:", sum(1 for r in rows if r["accepted"]))
    print("refused:", sum(1 for r in rows if r["refused"]))
    print("context_processed min/max/mean:", min(ctx), max(ctx), sum(ctx) / len(ctx))
    print(
        "span min/median/max:",
        f"{min(spans):.1f}",
        f"{sorted(spans)[len(spans) // 2]:.1f}",
        f"{max(spans):.1f}",
    )
    print("new turn values in final quarter:", sorted(late_new) or "none")
    print(
        "support coverage:",
        "NOT covered -- a new value appeared late"
        if uncovered
        else "final quarter was quiet (this certifies nothing)",
    )


if __name__ == "__main__":
    main(*sys.argv[1:])
