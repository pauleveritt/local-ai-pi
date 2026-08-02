"""Recompute this cycle's per-run table and aggregates from the two raw
checkpoints. Not a test -- a reproducibility aid the research record
cites, since its claims come from parsing pi_stdout via read_telemetry,
not from a trivial line count.

Usage (from the repo root, so `harness` is importable):
    PYTHONPATH=. uv run python \\
        docs/superpowers/research/2026-08-02-phase2-cycle2-recompute-summary.py \\
        ~/local-ai-pi-evidence/satyrn-cycle14-checkpoint-v2.jsonl \\
        ~/local-ai-pi-evidence/satyrn-phase2-cycle2-extension-n32.jsonl

The two raw checkpoints are outside Git (see tests/fixtures/README.md's
phase1-n48-telemetry-summary.json entry for their checksums); this script
cannot run without them.
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
                "errors": sum(1 for tc in tel.tool_calls if tc.is_error),
                "context_processed": tel.context_processed,
                "complete": tel.complete,
                "span": message_span(data["pi_stdout"]),
            }
        )
    return rows


def main(preserved_path: str, extension_path: str) -> None:
    rows = load(Path(preserved_path)) + load(Path(extension_path))
    for i, r in enumerate(rows, 1):
        tools = ",".join(f"{k}x{v}" for k, v in sorted(r["tool_names"].items()))
        print(
            f"{i:>2}: turns={r['turns']:>2} tools={r['tool_calls']:>2} ({tools:<14}) "
            f"errors={r['errors']} ctx={r['context_processed']:>6} "
            f"span={r['span']:.1f}s complete={r['complete']}"
        )
    turns = [r["turns"] for r in rows]
    ctx = [r["context_processed"] for r in rows]
    tools = sum((r["tool_names"] for r in rows), Counter())
    print()
    print("turn distribution:", dict(sorted(Counter(turns).items())))
    print("tool totals:", dict(tools))
    print("total errors:", sum(r["errors"] for r in rows))
    print("all complete:", all(r["complete"] for r in rows))
    print("context_processed min/max/mean:", min(ctx), max(ctx), sum(ctx) / len(ctx))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
