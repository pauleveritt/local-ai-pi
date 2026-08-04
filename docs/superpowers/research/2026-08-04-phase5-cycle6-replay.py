"""Replay the loop-breaker policy over every banked batch.

    PYTHONPATH=. uv run python \
        docs/superpowers/research/2026-08-04-phase5-cycle6-replay.py

**This is an analysis of the rule, not a test of the shipped code.** The
extension implements the policy in TypeScript (`.pi/extensions/loop-breaker.ts`)
and this reimplements it in Python. They can diverge, and no test here would
notice. The rule is deliberately trivial for that reason -- a window, a
threshold, and a key -- and the live smoke is what proves the extension.

What it answers, at zero model cost, over runs already recorded: where would
the breaker first have fired, and how many calls would it have prevented?
"""

import json
from pathlib import Path

from harness.checkpoint import load_checkpoint

WINDOW = 20
THRESHOLD = 5

EVIDENCE = Path.home() / "local-ai-pi-evidence"
BATCHES = {
    "cycle2 bare": "satyrn-phase5-cycle2-bare-n16",
    "cycle2 sdd": "satyrn-phase5-cycle2-sdd-orchestrator-n16",
    "cycle4 user-story bare": "satyrn-phase5-cycle4-user-story-bare-n16",
    "cycle4 user-story sdd": "satyrn-phase5-cycle4-user-story-sdd-n16",
    "cycle5 pilot (corrected prompt)": "satyrn-phase5-cycle5-pilot-n6-t300",
}


def call_key(event: dict) -> str:
    return f"{event.get('toolName')} {json.dumps(event.get('args'), sort_keys=True)}"


def replay(pi_stdout: str) -> tuple[int, int, int]:
    """(calls made, calls that would have been blocked, index of first block).

    Mirrors the extension: a sliding window of the last WINDOW *admitted*
    calls; a call whose key already appears THRESHOLD times in that window is
    blocked and does not enter the window.
    """
    recent: list[str] = []
    made = blocked = 0
    first = -1
    for line in pi_stdout.split("\n"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "tool_execution_start":
            continue
        made += 1
        key = call_key(event)
        if recent.count(key) >= THRESHOLD:
            blocked += 1
            if first < 0:
                first = made
            continue
        recent.append(key)
        if len(recent) > WINDOW:
            recent.pop(0)
    return made, blocked, first


def main() -> None:
    print(f"policy: window {WINDOW}, threshold {THRESHOLD}\n")
    for label, name in BATCHES.items():
        path = EVIDENCE / f"{name}.jsonl"
        if not path.is_file():
            print(f"## {label}\n\nMISSING: {path}\n")
            continue
        records = load_checkpoint(path)
        rows = [replay(record.pi_stdout) for record in records]
        tripped = [r for r in rows if r[1] > 0]
        print(f"## {label} — n={len(records)}")
        print(f"   runs where the breaker would fire: {len(tripped)}/{len(rows)}")
        print(f"   calls made in total: {sum(r[0] for r in rows)}")
        print(f"   calls it would have prevented: {sum(r[1] for r in rows)}")
        for i, (made, blocked_count, first) in enumerate(rows, 1):
            if blocked_count:
                print(
                    f"     run {i}: {made} calls, first block at call {first}, "
                    f"{blocked_count} prevented"
                )
        print()


if __name__ == "__main__":
    main()
